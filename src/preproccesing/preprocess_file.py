#Preproccess file from differents sources
import os
import pandas as pd
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader, CSVLoader 
from langchain_core.documents import Document

def identify_services_and_files(path_resources):
    #turn into pila
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
    #print(services_dic)  
    return(services_dic)

def save_info_services_files_numeric_formats(path_serv):
    excel_file = pd.read_excel(path_serv)
    txt_file = excel_file.to_string()
    return [Document(page_content=txt_file, metadata={"source": path_serv})]

def save_info_services_files_text_formats(services_dic):
    content_service={}
    #print(services_dic.items())
    for service, path_files in services_dic.items():
        # print(service)
        # print(path_files)
        content = []
        for path_serv in path_files:
            if path_serv.endswith(".pdf"):
                loader = PyPDFLoader(path_serv)
            elif path_serv.endswith(".txt"):
                loader = TextLoader(path_serv)
            elif path_serv.endswith(".docx"):
                loader = Docx2txtLoader(path_serv)
            elif path_serv.endswith(".csv"):
                loader = CSVLoader(path_serv)
            elif path_serv.endswith(".xlsx"):
                content.extend(save_info_services_files_numeric_formats(path_serv))
                continue
            else:
                continue
            #content.extend({"name":service})
            content.extend(loader.load())   
        content_service[service] = content
        #print(content)
    return(content_service)

def is_noise(text):
    text = text.lower()

    if "contenido" in text and "introducción" in text and "........" in text:
        return True

    return False
   
def clean_text(list_content_service):
    # print(type(list_content_service))
    # print(type(list_content_service["productos"]))
    content_product = {}
    for service, text in list_content_service.items():
        content = []
        full_text = ""
        metadata = None
        l = 0
        
        for t in range(len(text)):
            if l==0:
                metadata = text[t].metadata
                l=1
            if is_noise(text[t].page_content):
                continue
            full_text += text[t].page_content.lower() + " "
        full_text = (" ").join(full_text.split())
        content.append({
            "source": metadata.get("source"),
            "content": full_text
        })
        content_product[service] = content   
    #print(content_product)

    return(content_product)
               

def files_preprocessing(path_resources):
    services_dic = identify_services_and_files(path_resources)
    list_content_service = save_info_services_files_text_formats(services_dic)
    list_without_metadata = clean_text(list_content_service)
    return list_without_metadata

