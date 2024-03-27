"""
This file contains Rocketry app.
Add your tasks here, conditions etc. here.
"""
import asyncio
import uuid
from rocketry import Rocketry

from rocketry.args import Return, Session, Arg, FuncArg
from rocketry.conds import daily, time_of_week, after_success,minutely,secondly,hourly,every
import subir_archivo
import json
import os
import qdrant_funciones

app = Rocketry(config={"task_execution": "async"})
RUTA=''

@app.task(every('10 seconds', based="finish"))
async def do_permanently():
    "This runs for really long time"
    await asyncio.sleep(600000)

@app.task(every('2 seconds', based="finish"))
async def do_short():
    "This runs for short time"
    await asyncio.sleep(1)

@app.task(every('20 seconds', based="finish"))
async def do_long():
    "This runs for long time"
    await asyncio.sleep(60)

@app.task(every('10 seconds', based="finish"))
async def do_fail():
    "This fails constantly"
    await asyncio.sleep(10)
    raise RuntimeError("Whoops!")


##################################################################

def download_file(id,file_name, file_type,route):
    print('descargando archivo')
    if file_type=='application/vnd.google-apps.folder':
        print('es una carpeta')
    elif file_type=='application/vnd.google-apps.document':
        print('es un documento de google')
        datos_archivo=subir_archivo.export_pdf(id)
        #save file in local folder under file name
        subir_archivo.save_file(datos_archivo,RUTA+route+file_name+'.pdf')
        print('archivo descargado')
    else:
        print('descargando archivo')
        datos_archivo=subir_archivo.download_file(id)
        #save file in local folder under file name
        subir_archivo.save_file(datos_archivo,RUTA+route+file_name)
        print('archivo descargado')
        print('creando embeddings de archivo')
        qdrant_funciones.subir_archivo_qdrant(file_name,id)

def fill_kv_list():
    print('filling kv list')
    kv_list=open(RUTA+'drive_tracker/kv_drive/kv_drive.json','w')
    files=subir_archivo.search_file(kv=True)
    current_files=os.listdir('drive_tracker')
    print('archivos: ', current_files,'\n')
    #get list of files in current folder
    print('files: ',files,'\n')
    for id in files:
        if files[id]['file'] not in current_files:
           download_file(id,files[id]['file'],files[id]['type'],'drive_tracker/')

    json_files=json.dumps(files,indent=4)
    kv_list.write(json_files)


    
def update_kv_list(delete=False):
    print('actualizando kv list')
    if delete:
        kv_list=open(RUTA+'drive_tracker/kv_drive/kv_drive.json','w')
        kv_list.close()
    else:
        print('por ahora nada')
        
def update_spt(spt):
        print('actualizando spt')
        spt_file=open(RUTA+'drive_tracker/kv_drive/spt.txt','w')
        spt_file.write(str(spt))
        spt_file.close()

def borrar_archivo_local(change):
    kv_list=json.loads(open(RUTA+'drive_tracker/kv_drive/kv_drive.json','r').read())
    #print(kv_list)
    if change.get('fileId') in kv_list:
        print('borrando archivo '+kv_list[change.get('fileId')]['file']+' local')
        try:
            os.remove('drive_tracker/'+kv_list[change.get('fileId')]['file'])
        except:
            print('archivo ya fue borrado')
        print('borrando vectores de archivo')
        qdrant_funciones.borrar_archivo_qdrant(kv_list[change.get('fileId')]['file'])
        update_kv_list()
    print('archivo eliminado')

def bajar_archivo_a_local(change):
    kv_list=json.loads(open(RUTA+'drive_tracker/kv_drive/kv_drive.json','r').read())
    #print(kv_list[change.get('fileId')]['file'])
    #print(kv_list)
    print('id: ',change.get('fileId'))
    #print('nombre: ',kv_list[change.get('fileId')]['file'])
    #print('tipo: ',kv_list[change.get('fileId')]['type'])
    if change.get('fileId') not in kv_list:
        print('descargando archivo '+change.get('fileId')+' a local')
        file=subir_archivo.get_file(change.get('fileId'))
        print('file: ',file)
        download_file(change.get('fileId'),
                      file['name'],
                      file['mimeType'],
                      'drive_tracker/')
        update_kv_list()
    else:
        print('actualizando archivo '+kv_list[change.get('fileId')]['file']+' local')
        try:
            os.remove(RUTA+'drive_tracker/'+kv_list[change.get('fileId')]['file'])
            print('borrando embeddings antiguos')
            qdrant_funciones.borrar_archivo_qdrant(kv_list[change.get('fileId')]['file'])
        except:
            print('archivo ya fue borrado')
        download_file(change.get('fileId'),
                      kv_list[change.get('fileId')]['file'],
                      kv_list[change.get('fileId')]['type'],
                      'drive_tracker/')
        update_kv_list()
    print('archivo actualizado')

@app.cond()
def is_kv_list_empty():
    "checks the file that contains the filenames and drive ids"
    print('is kv list empty')
    kv_list=open(RUTA+'drive_tracker/kv_drive/kv_drive.json','r').readlines()
    #print(kv_list)
    if not kv_list:
        print('yes')
        fill_kv_list()
        return True
    print('no')
    return True

@app.cond()
def startPageToken_exists():
    "checks if the file spt.txt exists and has a value"
    print('startPageToken exists')
    spt=open(RUTA+'drive_tracker/kv_drive/spt.txt','r').read()
    if spt!='':
        print('yes')
        return True
    else:
        spt=subir_archivo.get_spt()
        open(RUTA+'drive_tracker/kv_drive/spt.txt','w').write(spt)
        return True

@app.task()
def check_update_from_drive_notification():
    "is called from the api by drive"
    print('buscando actualizaciones en drive')
    main_task()

#@app.task(hourly & is_kv_list_empty & startPageToken_exists)
@app.task(every('1 hour', based="finish") )#& is_kv_list_empty & startPageToken_exists)
def main_task():
    "tarea principal"
    print('main task')
    kv_list=open(RUTA+'drive_tracker/kv_drive/kv_drive.json','r').readlines()
    #print(kv_list)
    spt=int(open(RUTA+'drive_tracker/kv_drive/spt.txt','r').read())
    #print(spt)
    spt,changes=subir_archivo.get_changes(spt)
    print('NUEVO SPT ',spt)
    for change in changes:
        print('----cambio encontrado-----\n',change,'\n')
        if change.get('removed'):
            print('logica archivo eliminado')
            borrar_archivo_local(change)
        else:
            print('logica archivo creado/actualizado')
            bajar_archivo_a_local(change)
        print('------cambio procesado------')
    print('cambios actualizados')
    update_kv_list()
    update_spt(spt)


@app.task(every('1 hour'))
def refresh_channel():
    "refreshes the drive notification channel"
    id=str(uuid.uuid4())
    response=subir_archivo.watch(int(open(RUTA+'drive_tracker/kv_drive/spt.txt','r').read()),id)
    with open(RUTA+'drive_tracker/kv_drive/channel_id.txt','w') as old_channel_id:
        old_channel_id.write(response["resourceId"])

'''
@app.task(every('1 hour', based="finish"))
def main_task_2():
    if is_kv_list_empty() and startPageToken_exists():
        "tarea principal"
        print('main task')
        kv_list=open(RUTA+'drive_tracker/kv_drive/kv_drive.json','r').readlines()
        #print(kv_list)
        spt=int(open(RUTA+'drive_tracker/kv_drive/spt.txt','r').read())
        #print(spt)
        spt,changes=subir_archivo.get_changes(spt)
        print('NUEVO SPT ',spt)
        for change in changes:
            print('----cambio encontrado-----\n',change,'\n')
            if change.get('removed'):
                print('logica archivo eliminado')
                borrar_archivo_local(change)
            else:
                print('logica archivo creado/actualizado')
                bajar_archivo_a_local(change)
            print('------cambio procesado------')
        print('cambios actualizados')
        update_kv_list()
        update_spt(spt)
    else:
        raise RuntimeError("Whoops!")

'''
##################################################################
if __name__ == "__main__":
    # Run only Rocketry
    app.run()
