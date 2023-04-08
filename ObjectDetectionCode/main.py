import os
import requests
import firebase_admin
from firebase_admin import credentials, storage as fb_storage, db

# Replace with the path to your Firebase service account key JSON file
service_account_path = './serviceAccount.json'

# Replace with the path to your image file
image_path = './fire.jpeg'

# Replace with the destination filename for the image in Firebase Storage
destination_blob_name = 'fire.jpeg'

# Initialize the Firebase Admin SDK
cred = credentials.Certificate(service_account_path)
firebase_admin.initialize_app(cred, {
    'storageBucket': 'usersignin-fbecc.appspot.com',
    'databaseURL': 'https://usersignin-fbecc-default-rtdb.firebaseio.com'
})


def upload_image_to_storage(image_path, destination_blob_name):
    """Uploads an image to the specified Firebase Storage bucket."""

    # Replace with the URL of your Firebase Storage bucket
    storage_url = 'https://firebasestorage.googleapis.com/v0/b/usersignin-fbecc.appspot.com/o'

    # Replace with the access token for your Firebase service account
    access_token = 'your-firebase-service-account-access-token'

    # Construct the URL for the image upload request
    url = f"{storage_url}/{destination_blob_name}?uploadType=media&name={destination_blob_name}"

    # Set the headers for the image upload request
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'image/jpeg',
    }
    print(url)
    # Read the image file and send the upload request
    with open(image_path, 'rb') as f:
        response = requests.post(url, headers=headers, data=f)
        print(response)

    # Return the download URL for the uploaded image
    download_url = response.json().get('downloadTokens')
    return f"https://firebasestorage.googleapis.com/v0/b/usersignin-fbecc.appspot.com/o/{destination_blob_name}?alt=media&token={download_url}"


def store_image_url_in_realtime_db(image_url):
    """Store the image URL in Firebase Realtime Database."""

    # Replace 'latest_image' with the desired path in your Realtime Database
    latest_image_ref = db.reference('latest_image')
    latest_image_ref.set({
        'imageUrl': image_url
    })

    print("Image URL {} stored in Firebase Realtime Database.".format(image_url))


if __name__ == "__main__":
    # Upload the image to Firebase Storage
    image_url = upload_image_to_storage(image_path, destination_blob_name)
    print(f"Image URL: {image_url}")

    # Store the image URL in Firebase Realtime Database
    store_image_url_in_realtime_db(image_url)