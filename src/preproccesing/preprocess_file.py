#Preproccess file from differents sources
import os
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader, TextLoader, Docx2txtLoader

def identify_files(path_resources):
    #pila
    root = [path_resources]
    services_dic = {}
    while root:
        get_service = root.pop()
        #print(get_service)
        try:
            fodersfiles_in = os.listdir(get_service)
            #print(fodersfiles_in)
        except PermissionError:
            print(f"Sin permisos: {get_service}")
            continue
        except FileNotFoundError:
            print(f"No existe: {get_service}")
            continue
        except Exception as e: 
            print(f"Error accediendo a {get_service}: {e}") 
            continue

        for folderfile in fodersfiles_in:
            path_complete = os.path.join(get_service, folderfile)
            #print(path_complete)
            if os.path.isdir(path_complete):
                root.append(path_complete)
            if os.path.isfile(path_complete):
                service_gen = os.path.basename(os.path.dirname(path_complete))
                if service_gen not in services_dic:
                    services_dic[service_gen] = []

                services_dic[service_gen].append(path_complete)
    print(services_dic)  
    return(services_dic)


