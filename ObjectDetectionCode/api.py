from google.oauth2 import service_account
from google.cloud import datastore
from google.auth.transport.requests import Request
import cv2
import os
import requests
import firebase_admin
from firebase_admin import credentials, storage as fb_storage, db

class FirebaseStorageUploader:
    project_id = "usersignin-fbecc"
    bucket_name = "usersignin-fbecc.appspot.com"
    access_token = "3ebde5d70fa8171a9832b4d053068452b96a358"
    fire_count = 0
    people_count = 0    
    time_to_send = True
    call_count = 0
    # Replace with your Firebase private key file
    SERVICE_ACCOUNT_FILE = "./serviceAccount.json"

    # Firebase Cloud Messaging API URL
    FCM_API_URL = f"https://fcm.googleapis.com/v1/projects/{project_id}/messages:send"
    notification_smoke = {
                "title": "EmberEye detected smoke!",
                "body": "Click to check the app now!"
            }
    notification_fire = {
                "title": "EmberEye detected a fire!",
                "body": "Click to check the app now!"
            }
    cred = credentials.Certificate(SERVICE_ACCOUNT_FILE)
    firebase_admin.initialize_app(cred, {
        'storageBucket': 'usersignin-fbecc.appspot.com',
        'databaseURL': 'https://usersignin-fbecc-default-rtdb.firebaseio.com'
    })
    def get_latest_device_token(client):
        query = client.query(kind='tokens')
        query.order = ['-timestamp']
        results = list(query.fetch(limit=1))
        if results:
            return results[0]['token']
        else:
            return None

    def send_notification(notification):


        # Set up Datastore
        creds = service_account.Credentials.from_service_account_file(FirebaseStorageUploader.SERVICE_ACCOUNT_FILE)
        client = datastore.Client(project=FirebaseStorageUploader.project_id, credentials=creds)
        latest_token = FirebaseStorageUploader.get_latest_device_token(client)

        # Obtain an access token
        if creds.requires_scopes:
            creds = creds.with_scopes(['https://www.googleapis.com/auth/cloud-platform'])
        creds.refresh(Request())

        # Define the authentication headers
        headers = {
            "Authorization": "Bearer " + creds.token,
            "Content-Type": "application/json"
        }

        if latest_token:
            message = {
                "message": {
                    "token": latest_token,
                    "notification": notification
                }
            }

            # Send the message
            response = requests.post(FirebaseStorageUploader.FCM_API_URL, headers=headers, json=message)
            print("Push notification sent to token {}: {}".format(latest_token, response.json()))
        else:
            print("No device tokens found.")

    def upload_image(self, image, file_name):

        # Create the URL for the Firebase Storage upload API
        url = f"https://firebasestorage.googleapis.com/v0/b/{self.bucket_name}/o?name={file_name}"
        print(url)
        # Create the request headers with the access token and content type
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "image/jpeg"
        }

        # Encode the OpenCV image as JPEG and send a POST request to the Firebase Storage upload API
        _, encoded_image = cv2.imencode(".jpg", image)
        response = requests.post(url, headers=headers, data=encoded_image.tobytes())
        print(response)
         # Return the download URL for the uploaded image
        download_url = response.json().get('downloadTokens')
        down_url = f"https://firebasestorage.googleapis.com/v0/b/usersignin-fbecc.appspot.com/o/{file_name}?alt=media&token={download_url}"
        #"""Store the image URL in Firebase Realtime Database."""
        
        # Replace 'latest_image' with the desired path in your Realtime Database
        latest_image_ref = db.reference('latest_image')
        latest_image_ref.set({
            'imageUrl': down_url
        })

        print("Image URL {} stored in Firebase Realtime Database.".format(down_url))


        # Print the response from the Firebase Storage upload API
        print(response.text)
        
    def check_fire(self, frame, fire_detected, people_detected, smoke_detected):
        if fire_detected:
            self.fire_count += 1
            if self.fire_count >= 2 and self.people_count>1:
                # Upload the frame to Firebase Storage
                #file_name = f"fire_{self.fire_count}.jpg"
                self.upload_image(self, frame, 'fire.jpeg')
                print("Warning: Fire detected for two consecutive frames!")
                if(self.time_to_send):
                    self.send_notification(self.notification_fire) 
                    self.call_count += 1
                    if(self.call_count>0 and self.call_count<20):
                        self.time_to_send = False
                    else:
                        self.time_to_send = True

            elif self.fire_count >= 2 and self.people_count<1:
                # Upload the frame to Firebase Storage
                #file_name = f"fire_{self.fire_count}.jpg"
                self.upload_image(self, frame, "fire.jpeg")
                print("Alarm: Fire detected for two consecutive frames!")
                if(self.time_to_send):
                    self.send_notification(self.notification_fire) 
                    self.call_count += 1
                    if(self.call_count>0 and self.call_count<20):
                        self.time_to_send = False
                    else:
                        self.time_to_send = True
        elif smoke_detected:
                #file_name = f"fire_{self.fire_count}.jpg"
                self.upload_image(self, frame, "fire.jpeg")
                print("Alarm: Smoke detected!")
                if(self.time_to_send):
                    self.send_notification(self.notification_smoke) 
                    self.call_count += 1
                    if(self.call_count>0 and self.call_count<20):
                        self.time_to_send = False
                    else:
                        self.time_to_send = True
                        
        else:
            self.fire_count = 0
            self.time_to_send = True
        if people_detected:
            self.people_count += 1
        else:
            self.people_count = 0
