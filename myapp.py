
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image as KivyImage
from kivy.clock import Clock
import cv2
import numpy as np
import face_recognition
import os
from datetime import datetime
from kivy.graphics.texture import Texture
from controller import blink_led

class PlatformApp(BoxLayout):
    def __init__(self, **kwargs):
        super(PlatformApp, self).__init__(**kwargs)
        self.orientation = 'vertical'

        self.title = Label(text='Face Attendance', font_size=20, size_hint=(None, None), size=(1000, 50))
        self.add_widget(self.title)

        self.image = KivyImage()
        self.add_widget(self.image)
        self.label = Label(text='No one detected|Align', font_size=20, size_hint=(None, None), size=(1000, 50))
        self.add_widget(self.label)
        self.button = Button(text='Start',size_hint=(None, None), size=(1000, 50))
        self.button.bind(on_press=self.on_button_click)
        self.add_widget(self.button)


        self.cap = None  # Initialize cap here
        self.encodeListKnown = []
        self.classNames = []

    def on_button_click(self, instance):
        path = 'Training_images'
        images = []

        myList = os.listdir(path)
        print(myList)

        for cl in myList:
            curImg = cv2.imread(f'{path}/{cl}')
            images.append(curImg)
            self.classNames.append(os.path.splitext(cl)[0])

        print(self.classNames)

        self.encodeListKnown = []
        for img in images:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            encode = face_recognition.face_encodings(img)[0]
            self.encodeListKnown.append(encode)

        print('Encoding Complete')

        self.cap = cv2.VideoCapture(0)  # Move cap initialization here

        Clock.schedule_interval(self.update, 1.0 / 30.0)

    def update(self, dt):
        if self.cap is not None:
            success, img = self.cap.read()
            imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
            imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

            facesCurFrame = face_recognition.face_locations(imgS)
            encodesCurFrame = face_recognition.face_encodings(imgS, facesCurFrame)

            frame_width, frame_height = img.shape[1], img.shape[0]
            some_minimum_area_threshold = 0.01 * frame_width * frame_height

            for encodeFace, faceLoc in zip(encodesCurFrame, facesCurFrame):
                matches = face_recognition.compare_faces(self.encodeListKnown, encodeFace, tolerance=0.6)
                faceDis = face_recognition.face_distance(self.encodeListKnown, encodeFace)
                print(faceDis)
                matchIndex = np.argmin(faceDis)

                if matches[matchIndex] and faceDis[matchIndex] < 0.6:
                    name = self.classNames[matchIndex].upper()
                    y1, x2, y2, x1 = faceLoc
                    y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4

                    if (x2 - x1) * (y2 - y1) > some_minimum_area_threshold:
                        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.rectangle(img, (x1, y2 - 35), (x2, y2), (0, 255, 0), cv2.FILLED)
                        cv2.putText(img, name, (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)

                        with open('Attendance.csv', 'r+') as f:
                            myDataList = f.readlines()
                            nameList = []
                            dateList = []

                            for line in myDataList:
                                entry = line.strip().split(',')
                                nameList.append(entry[0])
                                dateList.append(entry[1])

                            now = datetime.now()
                            currentDate = now.strftime('%Y-%m-%d')
                            currentTime = now.strftime('%H:%M:%S')

                            if name in nameList and currentDate in dateList:
                                print(f"{name} has already been marked for attendance on {currentDate}.")
                                self.label.text = f"{name} has already been marked for attendance on {currentDate}."
                                blink_led(2)
                            else:
                                f.writelines(f'\n{name},{currentDate},{currentTime}')
                                print(f"{name} marked for attendance on {currentDate}.")
                                self.label.text = f"{name} marked for attendance on {currentDate}."
                                blink_led(1)

            # Convert the image to texture and update the Kivy Image widget
            buf = cv2.flip(img, 0)
            buf = buf.tostring()
            texture = Texture.create(size=(img.shape[1], img.shape[0]), colorfmt='bgr')
            texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
            self.image.texture = texture

    def on_stop(self):
        if self.cap is not None and self.cap.isOpened():
            self.cap.release()

class MyApp(App):
    def build(self):
        return PlatformApp()

if __name__ == '__main__':
    MyApp().run()
