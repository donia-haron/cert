from pyhtml2pdf import converter
from jinja2 import Environment, FileSystemLoader
import os
PATH = os.path.dirname(os.path.abspath(__file__))
import qrcode
import qrcode.image.svg
import tempfile
from flask import Flask, request, make_response
from flask_cors import CORS
import random
from google.cloud import storage
import datetime
storage_client = storage.Client()
from flask_expects_json import expects_json
import pathlib
import textwrap

random.seed()


app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

TEMPLATE_ENVIRONMENT = Environment(
    autoescape=False,
    #loader=FileSystemLoader(os.path.join(PATH, 'templates')),
    loader=FileSystemLoader(PATH),
    trim_blocks=False)

def render_template(template_filename, context):
    return TEMPLATE_ENVIRONMENT.get_template(template_filename).render(context)



def createIndividualCert(req):
    return render_template("HTML/Individual.html", {"request":req})

def createGroupCert(req):
    return render_template("HTML/Group.html", {"request":req})

def createCompanyCert(req):
    return render_template("HTML/Company.html", {"request":req})
def createBlockchainCert(req):
    return render_template("HTML/Blockchain.html", {"request":req})
def createBlockchainGroupCert(req):
    return render_template("HTML/group-blockchain.html", {"request":req})

@app.route("/api/v1/certificateGenerator", methods = ["POST"])
@expects_json({
    'type': 'object',
    'properties': {
        'certificateType': {'type': 'string'},
        'certificateDetails': {'type': 'object'},
        'targetName': {'type': 'string'},
        'targetBucket': {'type': 'string'},

    },
    'required': ['certificateType','certificateDetails','targetName','targetBucket']

})
def CertificateGenerator():
    request_json = request.get_json()

    if request_json['certificateType'].lower() == "individual":
        directory = tempfile.TemporaryDirectory()
        details = request_json["certificateDetails"]
        qr = qrcode.make(details["QRCodeData"], image_factory=qrcode.image.svg.SvgPathFillImage)
        with open(directory.name + "/QR.svg", "wb+") as f:
            qr.save(f)
        details["QRCodePath"] = directory.name + "/QR.svg"
        cert_HTML = createIndividualCert(details)
        cert_no = random.randint(0,999999999)
        with open(f"HTML/cert_{cert_no}.html", "w+") as f:
            f.write(cert_HTML)

        ## create PDF
        path = os.path.abspath(f"HTML/cert_{cert_no}.html")

        converter.convert(f'file:///{path}', f'{directory.name}/cert_{cert_no}.pdf')
        #converter.convert(f'file:///{path}', f"test_{cert_no}.pdf")
        bucket = storage_client.bucket(request_json["targetBucket"])

        with open(f'{directory.name}/cert_{cert_no}.pdf', "rb") as f:
            blob = bucket.blob(request_json["targetName"])
            blob.upload_from_file(f,content_type="application/pdf")

        #clean_up
        pathlib.Path(f"HTML/cert_{cert_no}.html").unlink(missing_ok= True)
        directory.cleanup()

        response = (
        {"status": "success", "fileBucket": request_json["targetBucket"], "fileName": request_json["targetName"], "timestamp": datetime.datetime.now()}, 200)

        return response
    elif request_json['certificateType'].lower() == "group":

        directory = tempfile.TemporaryDirectory()
        details = request_json["certificateDetails"]
        qr = qrcode.make(details["QRCodeData"], image_factory=qrcode.image.svg.SvgPathFillImage)
        with open(directory.name + "/QR.svg", "wb+") as f:
            qr.save(f)
        details["QRCodePath"] = directory.name + "/QR.svg"
        cert_HTML = createGroupCert(details)
        cert_no = random.randint(0,999999999)
        with open(f"HTML/cert_{cert_no}.html", "w+") as f:
            f.write(cert_HTML)

        ## create PDF
        path = os.path.abspath(f"HTML/cert_{cert_no}.html")

        converter.convert(f'file:///{path}', f'{directory.name}/cert_{cert_no}.pdf')
        #converter.convert(f'file:///{path}', f"test_{cert_no}.pdf")
        bucket = storage_client.bucket(request_json["targetBucket"])

        with open(f'{directory.name}/cert_{cert_no}.pdf', "rb") as f:
            blob = bucket.blob(request_json["targetName"])
            blob.upload_from_file(f,content_type="application/pdf")

        #clean_up
        pathlib.Path(f"HTML/cert_{cert_no}.html").unlink(missing_ok= True)
        directory.cleanup()

        response = (
        {"status": "success", "fileBucket": request_json["targetBucket"], "fileName": request_json["targetName"], "timestamp": datetime.datetime.now()}, 200)

        return response
    elif request_json['certificateType'].lower() == "company":

        directory = tempfile.TemporaryDirectory()
        cert_no = random.randint(0,999999999)

        details = request_json["certificateDetails"]
        qr = qrcode.make(details["QRCodeData"], image_factory=qrcode.image.svg.SvgPathFillImage)
        with open(directory.name + f"/QR_{cert_no}.svg", "wb+") as f:
            qr.save(f)
        details["QRCodePath"] = directory.name + f"/QR_{cert_no}.svg"

        ## add company logo
        bucketName = details["logoSourceBucket"]
        bucketPath = details["logoSourceName"]


        bucket = storage_client.bucket(bucketName)
        logo = bucket.get_blob(bucketPath)
        if logo.content_type == 'image/jpeg':
            extension = ".jpg"
        elif logo.content_type == 'image/png':
            extension= ".png"
        elif logo.content_type == 'image/svg+xml':
            extension= ".svg"
        else:
            return f"the company logo at bucket {bucketName} and path {bucketPath} is not jpg,png or svg", 401

        with open(directory.name + f"/logo_{cert_no}{extension}", "wb+") as f:
            logo.download_to_file(f)

        details["logoPath"] = directory.name + f"/logo_{cert_no}{extension}"

        cert_HTML = createCompanyCert(details)
        with open(f"HTML/cert_{cert_no}.html", "w+") as f:
            f.write(cert_HTML)

        ## create PDF
        path = os.path.abspath(f"HTML/cert_{cert_no}.html")

        converter.convert(f'file:///{path}', f'{directory.name}/cert_{cert_no}.pdf')
        #converter.convert(f'file:///{path}', f"test_{cert_no}.pdf")
        bucket = storage_client.bucket(request_json["targetBucket"])

        with open(f'{directory.name}/cert_{cert_no}.pdf', "rb") as f:
            blob = bucket.blob(request_json["targetName"])
            blob.upload_from_file(f,content_type="application/pdf")

        #clean_up
        pathlib.Path(f"HTML/cert_{cert_no}.html").unlink(missing_ok= True)
        directory.cleanup()

        response = (
        {"status": "success", "fileBucket": request_json["targetBucket"], "fileName": request_json["targetName"], "timestamp": datetime.datetime.now()}, 200)

        return response
    elif request_json['certificateType'].lower() == "blockchain":

        directory = tempfile.TemporaryDirectory()
        details = request_json["certificateDetails"]
        # generating cert QR code
        qr = qrcode.make(details["QRCodeData"], image_factory=qrcode.image.svg.SvgPathFillImage)
        with open(directory.name + "/QR.svg", "wb+") as f:
            qr.save(f)
        details["QRCodePath"] = directory.name + "/QR.svg"
        # generating fileHash QR
        QR_object = qrcode.QRCode(version = 10, image_factory=qrcode.image.svg.SvgPathFillImage)
        QR_object.add_data(details.get("fileHash",""))
        QR_object.make()
        fileHashQR = QR_object.make_image()
        with open(directory.name + "/fileHashQR.svg", "wb+") as f:
            fileHashQR.save(f)
        details["fileHashQRCodePath"] = directory.name + "/fileHashQR.svg"
        # generating transactionHash QR
        QR_object.clear()
        QR_object.add_data(details.get("transactionHash", ""))
        QR_object.make()
        transactionHashQR = QR_object.make_image()
        with open(directory.name + "/transactionHashQR.svg", "wb+") as f:
            transactionHashQR.save(f)
        details["transactionHashQRCodePath"] = directory.name + "/transactionHashQR.svg"

        ## divide up the hashes and insert spaces
        fileHash = textwrap.wrap(details.get("fileHash",""),32)
        fileHash = "<br>".join(fileHash)
        details["fileHash"] = fileHash
        transactionHash = textwrap.wrap(details.get("transactionHash",""),32)
        transactionHash = "<br>".join(transactionHash)
        details["transactionHash"] = transactionHash

        cert_HTML = createBlockchainCert(details)
        cert_no = random.randint(0,999999999)
        with open(f"HTML/cert_{cert_no}.html", "w+") as f:
            f.write(cert_HTML)

        ## create PDF
        path = os.path.abspath(f"HTML/cert_{cert_no}.html")

        converter.convert(f'file:///{path}', f'{directory.name}/cert_{cert_no}.pdf')
        #converter.convert(f'file:///{path}', f"test_{cert_no}.pdf")
        bucket = storage_client.bucket(request_json["targetBucket"])

        with open(f'{directory.name}/cert_{cert_no}.pdf', "rb") as f:
            blob = bucket.blob(request_json["targetName"])
            blob.upload_from_file(f,content_type="application/pdf")

        #clean_up
        pathlib.Path(f"HTML/cert_{cert_no}.html").unlink(missing_ok= True)
        directory.cleanup()

        response = (
        {"status": "success", "fileBucket": request_json["targetBucket"], "fileName": request_json["targetName"], "timestamp": datetime.datetime.now()}, 200)

        return response

    elif request_json['certificateType'].lower() == "blockchain_group":

        directory = tempfile.TemporaryDirectory()
        details = request_json["certificateDetails"]
        # generating cert QR code
        qr = qrcode.make(details["QRCodeData"], image_factory=qrcode.image.svg.SvgPathFillImage)
        with open(directory.name + "/QR.svg", "wb+") as f:
            qr.save(f)
        details["QRCodePath"] = directory.name + "/QR.svg"
        # generating fileHash QR
        QR_object = qrcode.QRCode(version=10, image_factory=qrcode.image.svg.SvgPathFillImage)
        QR_object.add_data(details.get("fileHash", ""))
        QR_object.make()
        fileHashQR = QR_object.make_image()
        with open(directory.name + "/fileHashQR.svg", "wb+") as f:
            fileHashQR.save(f)
        details["fileHashQRCodePath"] = directory.name + "/fileHashQR.svg"
        # generating transactionHash QR
        QR_object.clear()
        QR_object.add_data(details.get("transactionHash", ""))
        QR_object.make()
        transactionHashQR = QR_object.make_image()
        with open(directory.name + "/transactionHashQR.svg", "wb+") as f:
            transactionHashQR.save(f)
        details["transactionHashQRCodePath"] = directory.name + "/transactionHashQR.svg"

        ## divide up the hashes and insert spaces
        fileHash = textwrap.wrap(details.get("fileHash", ""), 32)
        fileHash = "<br>".join(fileHash)
        details["fileHash"] = fileHash
        transactionHash = textwrap.wrap(details.get("transactionHash", ""), 32)
        transactionHash = "<br>".join(transactionHash)
        details["transactionHash"] = transactionHash

        cert_HTML = createBlockchainGroupCert(details)
        cert_no = random.randint(0, 999999999)
        with open(f"HTML/cert_{cert_no}.html", "w+") as f:
            f.write(cert_HTML)

        ## create PDF
        path = os.path.abspath(f"HTML/cert_{cert_no}.html")

        converter.convert(f'file:///{path}', f'{directory.name}/cert_{cert_no}.pdf')
        # converter.convert(f'file:///{path}', f"test_{cert_no}.pdf")
        bucket = storage_client.bucket(request_json["targetBucket"])

        with open(f'{directory.name}/cert_{cert_no}.pdf', "rb") as f:
            blob = bucket.blob(request_json["targetName"])
            blob.upload_from_file(f, content_type="application/pdf")

        # clean_up
        pathlib.Path(f"HTML/cert_{cert_no}.html").unlink(missing_ok=True)
        directory.cleanup()

        response = (
            {"status": "success", "fileBucket": request_json["targetBucket"], "fileName": request_json["targetName"],
             "timestamp": datetime.datetime.now()}, 200)

        return response

    else:
        return f"certificateType {request_json['certificateType']} is not supported", 401




if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))


