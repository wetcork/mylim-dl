import pathlib
import requests
import json
import hashlib
import os
import sys

url_auth = "https://www.cloudschooling.it/loescher/api/v1/api-token-auth/"
url_index = "https://www.cloudschooling.it/mialim2/api/v1/book/sommari/"
url_attach = "https://api.loescher.it/api/v11/3rdparty/maieutical/books/assets/"
token_attach = "ecb4ccf847a5d38ff724fad284387b3a"

def main():
    token = login()
    download(token)

def login():
    user = input("\nInsert email: ")
    pswd = input("Insert password: ")

    pswd_md5 = hashlib.md5(pswd.encode('utf-8')).hexdigest()
    json_auth = {"username": user, "password": pswd_md5}

    auth = requests.post(url_auth, json=json_auth)
    auth_data = json.loads(auth.content)

    if "token" in auth_data:
        print("\nLogin successful")
        return auth_data["token"]
    else:
        print("\nLogin failed, try again")
        main()

def download(token):
    print("\nChoose a book:")
    index = requests.get(url_index, headers={"Authorization": "JWT " + token})
    index_data = json.loads(index.content)

    print("[A] Download all")

    for i in range(len(index_data)):
        if index_data[i]["tipologia"] == "c":
            print("[%s] %s" % (i, index_data[i]["opera"]["nome"]))

    book_id = input("\nBook ID: ")

    if book_id.lower() == "a":
        download_all(token)
    else:
        print("\n%s [%s]" % (index_data[int(book_id)]["opera"]["nome"], index_data[int(book_id)]["opera"]["isbn"]))
        print("[1] PDF")
        print("[2] Attachments")
        print("[3] PDF + Attachments")
        print("\nNOTE: Attachments will download all the book's extra contents, in most of the cases this will be a big download!")
        dwnl = input("\nInput: ")
        if (dwnl == "1"):
            pdf = True
            attach = False
        elif (dwnl == "2"):
            pdf = False
            attach = True
        elif (dwnl == "3"):
            pdf = True
            attach = True

        if (pdf):
            print("\nDownloading PDF...")
            pdf_name = "%s [%s].pdf" % (index_data[int(book_id)]["opera"]["nome"], index_data[int(book_id)]["opera"]["isbn"])
            pdf_path = "%s//%s" % (pathlib.Path(__file__).parent.resolve(), pdf_name)
            pdf_json = requests.get("https://www.cloudschooling.it" + index_data[int(book_id)]["opera"]["pdf"], headers={"Authorization": "JWT " + token})
            pdf_data = json.loads(pdf_json.content)
            pdf_url = pdf_data["url"]
            if not os.path.isfile(pdf_path):
                file_dl(pdf_url, pdf_path)
        
        if (attach):
            print("\nDownloading attachments...")
            attach_json = requests.get(url_attach + index_data[int(book_id)]["opera"]["bookshortcode"], headers={"AUTH_TOKEN": token_attach})
            attach_data = json.loads(attach_json.content)
            for i in range(len(attach_data["Files"])):
                attach_book = index_data[int(book_id)]["opera"]["nome"]
                attach_name = attach_data["Files"][i]["Etichetta"]
                attach_type = attach_data["Files"][i]["NomeSezione"]
                attach_ext = "." + attach_data["Files"][i]["Estensione"]

                if not attach_ext in attach_name:
                    attach_name = attach_name + attach_ext

                attach_dir = "%s//%s//%s//" % (pathlib.Path(__file__).parent.resolve(), attach_book, attach_type)
                attach_path = "%s%s" % (attach_dir, attach_name.replace(",", "").replace("?", "").replace("!", "").replace(":", ""))
                attach_url = attach_data["Files"][i]["URL"]

                if not os.path.isdir(attach_dir):
                    os.makedirs(attach_dir)
                if not os.path.isfile(attach_path):
                    file_dl(attach_url, attach_path)

        if input("\nDownload another book? [y/N]: ").lower() == "y":
            download(token)
        else:
            sys.exit(0)

def file_dl(url, file_path):
    try:
        with open(file_path, "wb") as f:
            r = requests.get(url, stream=True)
            total_length = r.headers.get("Content-Length")

            if total_length is None:
                f.write(r.content)
            else:
                dl = 0
                total_length = int(total_length)
                for data in r.iter_content(chunk_size=4096):
                    dl += len(data)
                    f.write(data)
                    done = int(50 * dl / total_length)
                    sys.stdout.write("\r[%s%s]" % ("#" * done, " " * (50 - done)))
                    sys.stdout.flush()
    except KeyboardInterrupt:
        os.remove(file_path)
        sys.exit("\n\nDownload cancelled")

def download_all(token):
    index = requests.get(url_index, headers={"Authorization": "JWT " + token})
    index_data = json.loads(index.content)

    print("Download all")
    print("[1] PDF")
    print("[2] Attachments")
    print("[3] PDF + Attachments")
    print("\nNOTE: Attachments will download all the book's extra contents, in most of the cases this will be a big download!")
    dwnl = input("\nInput: ")
    if (dwnl == "1"):
        pdf = True
        attach = False
    elif (dwnl == "2"):
        pdf = False
        attach = True
    elif (dwnl == "3"):
        pdf = True
        attach = True

    for i in range(len(index_data)):
        if index_data[i]["tipologia"] == "c":
            print("\n" + index_data[i]["opera"]["nome"])
            if (pdf):
                print("Downloading PDF...")
                pdf_name = "%s [%s].pdf" % (index_data[i]["opera"]["nome"], index_data[i]["opera"]["isbn"])
                pdf_path = "%s//%s" % (pathlib.Path(__file__).parent.resolve(), pdf_name)
                pdf_json = requests.get("https://www.cloudschooling.it" + index_data[i]["opera"]["pdf"], headers={"Authorization": "JWT " + token})
                pdf_data = json.loads(pdf_json.content)
                pdf_url = pdf_data["url"]
                if not os.path.isfile(pdf_path):
                    file_dl(pdf_url, pdf_path)
            
            if (attach):
                print("\nDownloading attachments...")
                attach_json = requests.get(url_attach + index_data[i]["opera"]["bookshortcode"], headers={'AUTH_TOKEN': token_attach})
                attach_data = json.loads(attach_json.content)
                for j in range(len(attach_data["Files"])):
                    attach_book = index_data[i]["opera"]["nome"]
                    attach_name = attach_data["Files"][j]["Etichetta"]
                    attach_type = attach_data["Files"][j]["NomeSezione"]
                    attach_ext = "." + attach_data["Files"][j]["Estensione"]

                    if not attach_ext in attach_name:
                        attach_name = attach_name + attach_ext

                    attach_dir = "%s//%s//%s//" % (pathlib.Path(__file__).parent.resolve(), attach_book, attach_type)
                    attach_path = "%s%s" % (attach_dir, attach_name.replace(",", "").replace("?", "").replace("!", "").replace(":", ""))
                    attach_url = attach_data["Files"][j]["URL"]

                    if not os.path.isdir(attach_dir):
                        os.makedirs(attach_dir)
                    if not os.path.isfile(attach_path):
                        file_dl(attach_url, attach_path)
            print("")

if __name__ == "__main__":
    print("myLIM Downloader v1.0")
    print("Created by WetCork")
    main()