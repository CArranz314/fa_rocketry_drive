from googleapiclient.discovery import build
from google.oauth2 import service_account
from google.auth import default
import time
from datetime import datetime


SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = ''
PARENT_FOLDER_ID =''
RUTA=''

def authenticate():
	creds= service_account.Credentials.from_service_account_file(RUTA+SERVICE_ACCOUNT_FILE,scopes=SCOPES)
	return creds

def upload_file(file_path,file_name):
	creds=authenticate()
	service = build('drive','v3',credentials=creds)

	file_metadata={
		'name':file_name,
		'parents':[PARENT_FOLDER_ID]
	}
	file = service.files().create(
	body=file_metadata,
	media_body=file_path
	).execute()

import io
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

##################################################### DOWNLOAD @@@@@@@@@@@@@@@@@@@
def download_file(file_id):
	try:
		creds=authenticate()
		service = build('drive','v3',credentials=creds)

		request = service.files().get_media(fileId=file_id)
		print(request)
		file = io.BytesIO()
		downloader = MediaIoBaseDownload(file, request)
		done = False
		while done is False:
			status, done = downloader.next_chunk()
			print(f"Download {int(status.progress() * 100)}.")

	except HttpError as error:
		print(f"An error occurred: {error}")
		file = None

	return file

def save_file(file,file_name):
	f= open(file_name, 'wb')
	f.write(file.getbuffer())
	f.close()
	print('archivo descargado')

def export_pdf(file_id):
	creds=authenticate()
	service = build('drive','v3',credentials=creds)
	request = service.files().export(fileId=file_id, mimeType='application/pdf')
	file = io.BytesIO()
	downloader = MediaIoBaseDownload(file, request)
	done = False
	while done is False:
		status, done = downloader.next_chunk()
		print(f"Download {int(status.progress() * 100)}.")

	return file

##################################################### LIST @@@@@@@@@@@@@@@@@@@
def search_file(file_name=None,kv=False):#kv es usado en rocketry_track_drive
	print('subir_archivo.search_file')
	creds=authenticate()

	try:
		service = build("drive", "v3", credentials=creds)
		files = []
		page_token = None
		query=''
		if file_name:
			query="name='"+file_name+"'"
		while True:
		# pylint: disable=maybe-no-member
			response = (
				service.files()
				.list(
					q=query,#query, vacia devuelve todo
					spaces="drive",
					fields="kind, nextPageToken, files(kind, id, name, fileExtension, mimeType,trashed, explicitlyTrashed, createdTime,modifiedTime, originalFilename)",
					pageToken=page_token,
				)
				.execute()
			)
			for file in response.get("files", []):
				#print(file)
				print(f'Found file: {file.get("name")}, {file.get("kind")}, {file.get("id")}, {file.get("mimeType")}, {file.get("trashed")}, {file.get("explicitlyTrashed")}')
		
			files.extend(response.get("files", []))
			page_token = response.get("nextPageToken", None)
			if page_token is None:
				break
	except HttpError as error:
		print(f"An error occurred: {error}")
		files = None
	if kv:
		files={file.get('id'):{'file':file.get('name'),'type':file.get('mimeType')} for file in files}
	return files

def get_file(file_id):
	try:
		creds=authenticate()
		service = build('drive','v3',credentials=creds)

		response = service.files().get(fileId=file_id,supportsAllDrives=True).execute()

	except HttpError as error:
		print(f"An error occurred: {error}")
		response={'error':error}
	return response
##################################################### DELETE @@@@@@@@@@@@@@@@@@@
def delete_file(file_id):
	try:
		creds=authenticate()
		service = build('drive','v3',credentials=creds)

		response = service.files().delete(fileId=file_id).execute()

	except HttpError as error:
		print(f"An error occurred: {error}")
		response={'error':error}
	return response

##################################################### TRASH @@@@@@@@@@@@@@@@@@@
def trash_file(file_id):
	try:
		creds=authenticate()
		service = build('drive','v3',credentials=creds)

		body = {'trashed': True}
		response = service.files().update(fileId=file_id, body=body).execute()

	except HttpError as error:
		print(f"An error occurred: {error}")
		response={'error':error}
	return response

##################################################### EMPTY TRASH @@@@@@@@@@@@@@@@@@@
def empty_trash():
	try:
		creds=authenticate()
		service = build('drive','v3',credentials=creds)

		response = service.files().emptyTrash().execute()

	except HttpError as error:
		print(f"An error occurred: {error}")
		response={'error':error}
	return response

##################################################### GET CHANGES @@@@@@@@@@@@@@@@@@@
def get_spt():
	print('getting spt')
	creds,_= default()
	#print(creds.__dict__, _)
	creds2=authenticate()
	#print(creds2.__dict__)
	try:
		service= build('drive','v3',credentials=creds2)
		
		response = service.changes().getStartPageToken(
										supportsAllDrives=True
										).execute()
		print(response.get('startPageToken'))
	except HttpError as error:
		print('error: ',error)
		response= None
	
	return response.get('startPageToken')

def get_changes(spt):
	creds=authenticate()
	try:
		service= build('drive','v3',credentials=creds)
		page_token=spt
		while page_token is not None:

			response = service.changes().list(
										pageToken=spt,
										#fields='*',
										includeRemoved=True,
										includeCorpusRemovals=True,
										spaces='drive'
										).execute()
			#print('response: ', response)
			for change in response.get('changes'):
				#print('nuevo cambio: ',change,'\n')
				#print('archivo ', service.files().get(fileId=change.get('fileId')).execute())
				...
			if 'newStartPageToken' in response:
				spt=int(response.get('newStartPageToken'))
				page_token=response.get('pageToken')

	except HttpError as error:
		print('error: ',error)
		spt=None
	
	return spt,response.get('changes')

def get_revisions(file_id):
	creds=authenticate()
	try:
		service= build('drive','v3',credentials=creds)
		response = service.revisions().list(
										fileId=file_id
										).execute()
		print('revisiones: ', response)
		response = service.revisions().get(
										fileId=file_id,
										revisionId=response['revisions'][-1]['id']
										).execute()
		print('ultima revision: ', response)
	except HttpError as error:
		print('error: ',error)
		response=None
	return response

#tambien necesita spt
def watch(spt,uuid):
	'''
	respuesta:
	{'kind': 'api#channel', 'id': 'probando-probando-607', 
	'resourceId': 'Q060HOkce5xsAcgMu9LOwg7O2xI', 
	'resourceUri': 'https://www.googleapis.com/drive/v3/changes?alt=json&includeCorpusRemovals=true&includeRemoved=true&pageToken=145&spaces=drive', 
	'expiration': '1711534523000'}
	'''
	creds=authenticate()
	try:
		service= build('drive','v3',credentials=creds)
		file_metadata = { 
    "resourceUri": "https://www.googleapis.com/drive/v3/files/"+PARENT_FOLDER_ID,
    "kind": "api#channel", 
    "resourceId": PARENT_FOLDER_ID, 
    "payload": True, 
    #"expiration": "A String", # Date and time of notification channel expiration, expressed as a Unix timestamp, in milliseconds. Optional.
    "address": "https://rag.iort.io/index/",#"https://europe-west1-unique-poetry-417111.cloudfunctions.net/receptor-webhook-2", #"http://164.90.197.167:8000/" # The address where notifications are delivered for this channel.
    "type": "web_hook", 
    "id": uuid, 
  }
		response = service.changes().watch(
										pageToken=spt,
										body=file_metadata,
										includeRemoved=True,
										includeCorpusRemovals=True,
										spaces='drive'
										).execute()
	except HttpError as error:
		print('error: ',error)
		response=None
	return response

def file_watch(file_id,uuid):
	creds=authenticate()
	ahora=int(datetime.timestamp(datetime.now()))
	print(ahora)
	try:
		service= build('drive','v3',credentials=creds)
		file_metadata = { # An notification channel used to watch for resource changes.
	"resourceUri": "https://www.googleapis.com/drive/v3/files/"+file_id, # A version-specific identifier for the watched resource.
	"kind": "api#channel", # Identifies this as a notification channel used to watch for changes to a resource, which is "api#channel".
	"resourceId": file_id, # An opaque ID that identifies the resource being watched on this channel. Stable across different API versions.
	"payload": True, # A Boolean value to indicate whether payload is wanted. Optional.
	#"token": "A String", # An arbitrary string delivered to the target address with each notification delivered over this channel. Optional.
	#"params": { # Additional parameters controlling delivery channel behavior. Optional.
	#  "a_key": "A String", # Declares a new parameter by name.
	#},
	"expiration": (ahora+604800)*1000 ,#"A String", # Date and time of notification channel expiration, expressed as a Unix timestamp, in milliseconds. Optional.
	"address": "https://europe-west1-unique-poetry-417111.cloudfunctions.net/receptor-webhook-2",
	 "type": "web_hook", # The type of delivery mechanism used for this channel.
    "id": uuid, # A UUID or similar unique string that identifies this channel.
		}
		response = service.files().watch(
										fileId=file_id,
										body=file_metadata
										).execute()
	except HttpError as error:
		print('error: ',error)
		response=None
	return response


def get_drive(drive_id):
	creds=authenticate()
	try:
		service= build('drive','v3',credentials=creds)
		response = service.drives().get(
										driveId=drive_id
										).execute()
	except HttpError as error:
		print('error: ',error)
		response=None
	return response


################################################################################
def get_changes_2(spt):
	creds=authenticate()
	try:
		service= build('drive','v3',credentials=creds)
		page_token=spt
		while page_token is not None:

			response = service.changes().list(
										pageToken=spt,
										#fields='*',
										includeRemoved=True,
										includeCorpusRemovals=True,
										spaces='drive'
										)
			print('request',response.__dict__)
			response=response.execute()
			print('response: ', response)
			#print('response: ', response)
			for change in response.get('changes'):
				#print('nuevo cambio: ',change,'\n')
				#print('archivo ', service.files().get(fileId=change.get('fileId')).execute())
				...
			if 'newStartPageToken' in response:
				spt=int(response.get('newStartPageToken'))
				page_token=response.get('pageToken')

	except HttpError as error:
		print('error: ',error)
		spt=None
	
	return spt,response.get('changes')


