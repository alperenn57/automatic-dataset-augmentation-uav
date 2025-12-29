from arayuz import Ui_MainWindow
from PyQt5.QtWidgets import QApplication, QMainWindow
import sys, os, cv2, torch, yt_dlp

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.qtTasarim = Ui_MainWindow()
        self.qtTasarim.setupUi(self)
        self.qtTasarim.pushButton.clicked.connect(self.start_processing)

    def start_processing(self):
        url = self.qtTasarim.lineEdit_2.text().strip()
        model_path = self.qtTasarim.lineEdit.text().strip()
        if not url or not model_path:
            print("URL veya model yolu eksik.")
            return
        self.process_video(url, model_path)

    def process_video(self, url, model_path):
        ydl_opts = {'format': 'bestvideo[height<=720]', 'quiet': True, 'outtmpl': 'temp_video.mp4'}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except Exception as e:
            print("Video indirilemedi:", e); return

        cap = cv2.VideoCapture('temp_video.mp4')
        if not cap.isOpened():
            print("Video açılamadı"); return

        try:
            model = torch.hub.load('ultralytics/yolov5', 'custom', path=model_path, verbose=False)
        except Exception as e:
            print("Model yüklenemedi:", e); cap.release(); return

        ss_folder = "screenshots"; label_folder = "labels"
        os.makedirs(ss_folder, exist_ok=True); os.makedirs(label_folder, exist_ok=True)

        frame_rate = cap.get(cv2.CAP_PROP_FPS) or 25
        frame_interval = max(1, int(frame_rate * 3))

        while True:
            ret, frame = cap.read()
            if not ret: break
            try:
                results = model(frame)
                detections = results.pandas().xyxy[0]
            except Exception:
                detections = None

            if detections is not None and not detections.empty:
                fc = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
                ffile = os.path.join(ss_folder, f'frame_{fc}.jpg')
                lfile = os.path.join(label_folder, f'frame_{fc}.txt')
                cv2.imwrite(ffile, frame)
                unique=set()
                with open(lfile,'w') as f:
                    for _,row in detections.iterrows():
                        cid=int(row['class'])
                        xc=(row['xmin']+row['xmax'])/2/frame.shape[1]
                        yc=(row['ymin']+row['ymax'])/2/frame.shape[0]
                        w=(row['xmax']-row['xmin'])/frame.shape[1]
                        h=(row['ymax']-row['ymin'])/frame.shape[0]
                        t=f"{cid} {xc} {yc} {w} {h}\n"
                        if t not in unique:
                            unique.add(t); f.write(t)
                print("Kaydedildi:", ffile)
            pos = cap.get(cv2.CAP_PROP_POS_FRAMES)
            cap.set(cv2.CAP_PROP_POS_FRAMES, pos + frame_interval)

        cap.release()
        if os.path.exists('temp_video.mp4'): os.remove('temp_video.mp4')
        print("Video işleme tamam. Editör açılıyor.")
        self.edit_annotations(ss_folder, label_folder)

    def edit_annotations(self, img_folder, label_folder):
        imgs = sorted([f for f in os.listdir(img_folder) if f.lower().endswith(('.jpg','.png'))])
        if not imgs:
            print("Resim yok"); return

        for img_file in imgs:
            img_path = os.path.join(img_folder, img_file)
            anno_path = os.path.join(label_folder, os.path.splitext(img_file)[0]+".txt")
            img = cv2.imread(img_path); h,w = img.shape[:2]

            # model boxes oku
            model_boxes=[]
            if os.path.exists(anno_path):
                with open(anno_path,'r') as f:
                    for line in f:
                        d=line.strip().split()
                        if len(d)<5: continue
                        cid=int(d[0]); xc, yc, ww, hh = map(float, d[1:5])
                        x1=int((xc-ww/2)*w); y1=int((yc-hh/2)*h)
                        x2=int((xc+ww/2)*w); y2=int((yc+hh/2)*h)
                        model_boxes.append([cid,x1,y1,x2,y2])

            manual_boxes=[]
            current_rect=None
            drawing=False
            ix=iy=0

            def mouse_cb(event,x,y,flags,param):
                nonlocal ix,iy,drawing,current_rect,manual_boxes
                if event==cv2.EVENT_LBUTTONDOWN:
                    drawing=True; ix,iy=x,y; current_rect=None
                elif event==cv2.EVENT_MOUSEMOVE and drawing:
                    x1,y1=max(0,min(ix,x)), max(0,min(iy,y))
                    x2,y2=min(w-1,max(ix,x)), min(h-1,max(iy,y))
                    current_rect=(x1,y1,x2,y2)
                elif event==cv2.EVENT_LBUTTONUP:
                    drawing=False
                    x1,y1=max(0,min(ix,x)), max(0,min(iy,y))
                    x2,y2=min(w-1,max(ix,x)), min(h-1,max(iy,y))
                    if abs(x2-x1)>5 and abs(y2-y1)>5:
                        manual_boxes.append([0,x1,y1,x2,y2])
                    current_rect=None

            win="Etiket Düzenleyici"
            cv2.namedWindow(win, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(win, min(1280,w), min(720,h))
            cv2.setMouseCallback(win, mouse_cb)
            print(f"Düzenle: {img_file} (S=save, R=remove, Z=model sil, C=exit)")

            while True:
                disp = img.copy()
                # model
                for cid,x1,y1,x2,y2 in model_boxes:
                    cv2.rectangle(disp,(x1,y1),(x2,y2),(0,255,0),2)
                    cv2.putText(disp,f"Model {cid}",(x1,max(15,y1-6)),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0,255,0),1)
                # manual
                for cid,x1,y1,x2,y2 in manual_boxes:
                    overlay=disp.copy()
                    cv2.rectangle(overlay,(x1,y1),(x2,y2),(0,0,255),-1)
                    cv2.addWeighted(overlay,0.45,disp,0.55,0,disp)
                    cv2.rectangle(disp,(x1,y1),(x2,y2),(0,0,255),2)
                # temp
                if current_rect:
                    x1,y1,x2,y2 = current_rect
                    overlay=disp.copy()
                    cv2.rectangle(overlay,(x1,y1),(x2,y2),(0,0,255),-1)
                    cv2.addWeighted(overlay,0.45,disp,0.55,0,disp)
                    cv2.rectangle(disp,(x1,y1),(x2,y2),(0,0,255),2)
                    cv2.putText(disp,"Çiziliyor...",(x1,max(15,y1-6)),cv2.FONT_HERSHEY_SIMPLEX,0.6,(0,0,255),2)

                cv2.imshow(win, disp)
                key = cv2.waitKey(20) & 0xFF
                if key==ord('s'):
                    all_boxes = model_boxes + manual_boxes
                    with open(anno_path,'w') as f:
                        for cid,x1,y1,x2,y2 in all_boxes:
                            xc = ((x1+x2)/2)/w
                            yc = ((y1+y2)/2)/h
                            ww = (x2-x1)/w
                            hh = (y2-y1)/h
                            f.write(f"{cid} {xc} {yc} {ww} {hh}\n")
                    print("Kaydedildi:", img_file)
                    break
                elif key==ord('r'):
                    try: os.remove(img_path)
                    except: pass
                    try: os.remove(anno_path)
                    except: pass
                    print("Silindi:", img_file)
                    break
                elif key==ord('z'):
                    model_boxes=[]
                    print("Model etiketleri silindi. Şimdi manuel çizebilirsin.")
                elif key==ord('c'):
                    print("İptal edildi."); cv2.destroyAllWindows(); return

            cv2.destroyAllWindows()

        print("Bitti.")

if __name__=="__main__":
    app=QApplication(sys.argv)
    window=MainWindow()
    window.show()
    sys.exit(app.exec())
