import rocketry as rk
from rocketry.args import Return, Session, Arg, FuncArg
from rocketry.conds import daily, time_of_week, after_success,minutely,secondly,hourly
import subir_archivo
import json
import os
import qdrant_funciones

app=rk.Rocketry(config={'execution_task':'async'})


def download_file(id,file_name, file_type,route):
    print('descargando archivo')
    if file_type=='application/vnd.google-apps.folder':
        print('es una carpeta')
    elif file_type=='application/vnd.google-apps.document':
        print('es un documento de google')
        datos_archivo=subir_archivo.export_pdf(id)
        #save file in local folder under file name
        subir_archivo.save_file(datos_archivo,route+file_name+'.pdf')
        print('archivo descargado')
    else:
        print('descargando archivo')
        datos_archivo=subir_archivo.download_file(id)
        #save file in local folder under file name
        subir_archivo.save_file(datos_archivo,route+file_name)
        print('archivo descargado')
        print('creando embeddings de archivo')
        qdrant_funciones.subir_archivo_qdrant(file_name)

def fill_kv_list():
    print('filling kv list')
    kv_list=open('drive_tracker/kv_drive/kv_drive.json','w')
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
        kv_list=open('drive_tracker/kv_drive/kv_drive.json','w')
        kv_list.close()
    else:
        print('por ahora nada')
        
def update_spt(spt):
        print('actualizando spt')
        spt_file=open('drive_tracker/kv_drive/spt.txt','w')
        spt_file.write(str(spt))
        spt_file.close()

def borrar_archivo_local(change):
    kv_list=json.loads(open('drive_tracker/kv_drive/kv_drive.json','r').read())
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
    kv_list=json.loads(open('drive_tracker/kv_drive/kv_drive.json','r').read())
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
            os.remove('drive_tracker/'+kv_list[change.get('fileId')]['file'])
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
    print('is kv list empty')
    kv_list=open('drive_tracker/kv_drive/kv_drive.json','r').readlines()
    #print(kv_list)
    if not kv_list:
        print('yes')
        fill_kv_list()
        return True
    print('no')
    return True

@app.cond()
def startPageToken_exists():
    print('startPageToken exists')
    spt=open('drive_tracker/kv_drive/spt.txt','r').read()
    if spt!='':
        print('yes')
        return True
    else:
        spt=subir_archivo.get_spt()
        open('drive_tracker/kv_drive/spt.txt','w').write(spt)
        return True


@app.task(hourly & is_kv_list_empty & startPageToken_exists)
def task():
    print('main task')
    kv_list=open('drive_tracker/kv_drive/kv_drive.json','r').readlines()
    #print(kv_list)
    spt=int(open('drive_tracker/kv_drive/spt.txt','r').read())
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

    


if __name__ == "__main__":
    
    print('inicio')
    
    app.run()
