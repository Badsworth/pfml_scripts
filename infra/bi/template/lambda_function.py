import boto3
import json
import csv
import urllib
import boto3.session
import os
import time
import logging
from botocore.exceptions import ClientError

s3 = boto3.client("s3")
s3_resource = boto3.resource('s3')
#s3 = boto3.resource('s3')

# adding variable so that the lambda is environment agnostic
environment = os.environ.get("ENVIRONMENT")

def lambda_handler(event, context):

    EachRowCount=[]
    RowCount=[]
    processedfileslist=[]
    ActualFileRowCount=0
    ProcessFileRowCount=0
    client = boto3.client('s3')
    
    count=0
    Files=""
    csvSourceFilename=""
    csvDestinationFile=""
    csvDestinationPATH=""
    csv_Source_Absenceleavecases=""
    csv_Source_Taskreport=""
    DestinationPATHList=[]
    processedfiles_vendor_details="processedfiles/VBI_REQUESTEDABSENCE/"
    processedfiles_vendor_names="processedfiles/VBI_TASKREPORT_SOM/"
    vendor_details="VBI_REQUESTEDABSENCE"
    vendor_names="VBI_TASKREPORT_SOM"
    DestinationBucketName=f"massgov-pfml-{environment}-redshift-daily-import"
    s3object = boto3.resource('s3')
    # Here we create a new session per thread
    session = boto3.session.Session()
    s3_resource = session.resource('s3')
    if event:
        logging.warn("Event :%s", event)
        time.sleep(10)
        ActualFileRowCount=0
        vendor_detailsRowCount=0
        vendor_namesRowCount=0
        LenthOfObjectsInFile=0
        filenameLenghtcsv=0
        filename=""
        file_obj = event["Records"][0]
        
        
        bucket_name = str(file_obj['s3']['bucket']['name'])
        filename = str(file_obj['s3']['object']['key'])
        filenameLength=len(filename.split("/"))
        logging.warn("filenameLength::::%s",filenameLength)
        for i in range(filenameLength):
            filenameLenghtcsv=i
        logging.warn("filename::::%s",filename)
        csvSourceFilename=filename.split("/")[filenameLenghtcsv]
        csvSourceFolder=filename.split("/")[0]
        logging.warn("csvSourceFolder :%s", csvSourceFolder)
        logging.warn("csvSourceFilename :%s", csvSourceFilename)
        logging.warn("bucket_name :%s", bucket_name)
        old_bucket = s3_resource.Bucket(bucket_name )
        new_bucket = s3_resource.Bucket(DestinationBucketName )
        fileObj = s3.get_object(Bucket =bucket_name, Key=filename)
        file_content = fileObj["Body"].read().decode('utf-8')

        strfilecontent=str(file_content)
        strfilecontentlist=strfilecontent.splitlines()

        ActualFileRowCount=len(strfilecontentlist)
        logging.warn("Number of Rows in file::::%s",len(strfilecontentlist))


        EachRowCount.append(file_content)
 
        #Check if file exists in Process Folder
        
        result_vendor_details = s3.list_objects(Bucket = DestinationBucketName, Prefix=processedfiles_vendor_details)
        folderandfilesLength=result_vendor_details.get("Contents")
        logging.warn("Length of Contents::::result_vendor_details:::::%s",len(folderandfilesLength))
        logging.warn("Contents::::result_vendor_details::%s",folderandfilesLength)

        logging.warn("len(folderandfilesLength):::LENGTH OF Destination Folder:::result_vendor_details:::%s",len(folderandfilesLength))

        logging.warn("Source Contents for File:::result_vendor_details::%s",folderandfilesLength[0].get("Key"))

        Folder_vendor_details_PATH=folderandfilesLength[0].get("Key")
        logging.warn("Source Files======folderandfilesLength[1].get(Key)===>:result_vendor_details:::::%s",Folder_vendor_details_PATH)
        if not Folder_vendor_details_PATH.endswith("csv"):
           logging.warn("Folder_vendor_details::::::result_vendor_details:::::::%s",Folder_vendor_details_PATH)
           DestinationPATHList.append(Folder_vendor_details_PATH)

        result_vendor_names = s3.list_objects(Bucket = DestinationBucketName, Prefix=processedfiles_vendor_names)
        folderandfilesLength=result_vendor_names.get("Contents")
        logging.warn("Lenghof Contents::_vendor_names:::%s",len(folderandfilesLength))
        logging.warn("Contents:::_vendor_names:::%s",folderandfilesLength)

        logging.warn("len(folderandfilesLength):::LENGTH OF Destination Folder::_vendor_names:::::%s",len(folderandfilesLength))

        logging.warn("Source Contents for File:::_vendor_names:::%s",folderandfilesLength[0].get("Key"))
        logging.warn("IIIIIIIIIIIIIIII_vendor_namesII %s",folderandfilesLength[0])
        Folder_vendor_names_PATH=folderandfilesLength[0].get("Key")
        logging.warn("Source Folder_vendor_names======folderandfilesLength[1].get(Key)===>:::::_vendor_names:::%s",Folder_vendor_names_PATH)
        if not Folder_vendor_names_PATH.endswith("csv"):
           logging.warn("Folder_vendor_names::::::::_vendor_names:::::%s",Folder_vendor_names_PATH)
           DestinationPATHList.append(Folder_vendor_names_PATH)
        copy_source = {
                      'Bucket': bucket_name,
                      'Key': csvSourceFilename
                     }
        logging.warn("bucket_name:::%s",bucket_name)#old Bucket
        logging.warn("Source File Name::%s",filename)#obj.key
        logging.warn("csvSourceFilename::::%s",csvSourceFilename)#old file name
        logging.warn("Destination Path::Folder_vendor_details_PATH:::::%s",Folder_vendor_details_PATH)
        logging.warn("Destination Path::Folder_vendor_names_PATH:::::%s",Folder_vendor_names_PATH)
        try:
            csvSourceFolderwithSlash=csvSourceFolder+"/"
            if filename.endswith('.csv'):
                old_source = { 'Bucket': bucket_name,
                           'Key': filename}
                 
                if  vendor_names in filename:
                    logging.warn("In vendor_names:::::::::::::::")
                    # replace the prefix
                    logging.warn("vendor_names csv file not found then copying new File:::")
                    logging.warn("csvSourceFolderwithSlash::::%s",csvSourceFolderwithSlash)
                    logging.warn("Folder_vendor_names_PATH:::%s",Folder_vendor_names_PATH)
                    new_key = filename.replace(csvSourceFolderwithSlash, Folder_vendor_names_PATH)
                    new_key = Folder_vendor_names_PATH+ csvSourceFilename
                    new_obj = new_bucket.Object(new_key)
                    logging.warn("obj.key::%s",filename)
                    logging.warn("new_key::%s",new_key)
                    bucket = s3object.Bucket(DestinationBucketName)
                    objs = list(bucket.objects.filter(Prefix=Folder_vendor_names_PATH))
                    logging.warn("**************len(objs)***vendor_names************ %s",len(objs))
                    for i in range(0, len(objs)):
                        logging.warn("%s", objs[i].key)
                        logging.warn("objs[i].key::filename:::%s",objs[i].key)
                        if vendor_names in objs[i].key:
                            filename=objs[i].key
                            logging.warn("Before if condition::vendor_names::filename:%s",filename)
                            if filename.endswith("csv") and vendor_names in filename:
                                fileObj = client.get_object(Bucket =DestinationBucketName, Key=filename)
                                file_content = fileObj["Body"].read().decode('utf-8')
                                strfilecontent=str(file_content)
                                strfilecontentlist=strfilecontent.splitlines()
                                # logging.warn("strfilecontentlist::vendor_names:::%s",str(strfilecontentlist))
                                vendor_namesRowCount=len(strfilecontentlist)
                                logging.warn("Number of Rows in file::vendor_names::%s",len(strfilecontentlist))
                                vendor_namesRowCount=len(strfilecontentlist)
                                logging.warn("ActualFileRowCount::::%s",ActualFileRowCount)
                                logging.warn("vendor_detailsRowCount::::%s",vendor_namesRowCount)
                                if ActualFileRowCount > vendor_namesRowCount:
                                    #If New file Number of Row's is greater then old file then copy the New file  
                                    logging.warn("I AM IN ActualFileRowCount > vendor_namesRowCount")
                                    response = client.list_objects_v2(Bucket=DestinationBucketName, Prefix=Folder_vendor_names_PATH)
                                    for object in response['Contents']:
                                      logging.warn('Deleting: %s', object['Key'])
                                      if (vendor_names in object['Key']) and object['Key'].endswith("csv"):
                                         client.delete_object(Bucket=DestinationBucketName, Key=object['Key'])
                                         print("File::::"+csvSourceFilename+":::Deleted into processedfiles/vendor_names/!!!!!!!!")
                                    new_obj.copy(old_source)
                                    logging.warn("obj.key::%s",filename)
                                    logging.warn("new_key::%s",new_key)
                                    print("File::::"+csvSourceFilename+":::copied into processedfiles/vendor_names/!!!!!!!!")
                                else:
                                    logging.warn("vendor_details csv File not found then copying NEW File:processedfiles/vendor_names/:::")
                            elif filename.endswith("csv"):
                                #If CSV File not exists then Copying the new file
                                logging.warn("vendor_names csv file not found then copying new File::processedfiles/vendor_names/::::")
                                new_obj.copy(old_source)
                                logging.warn("obj.key::%s",filename)
                                logging.warn("new_key::%s",new_key)
                                print("File::::"+csvSourceFilename+":::copied into processedfiles/vendor_names/!!!!!!!!")
                            
                            elif len(objs) == 1:
                                logging.warn("vendor_names csv file not found and len(objs) == 1 then copying new File::processedfiles/vendor_names/::::")
                                new_obj.copy(old_source)
                                logging.warn("obj.key::%s",filename)
                                logging.warn("new_key::%s",new_key)
                                print("File::::"+csvSourceFilename+":::copied into processedfiles/vendor_names/!!!!!!!!")
                                
                elif vendor_details in filename:
                    logging.warn("In vendor_details:::::::::::::::")
                    #replace the prefix
                    logging.warn("vendor_details csv File not found then copying NEW File::::")
                    logging.warn("csvSourceFolderwithSlash::::%s",csvSourceFolderwithSlash)
                    logging.warn("Folder_vendor_details_PATH:::%s",Folder_vendor_details_PATH)
                    new_key = filename.replace(csvSourceFolderwithSlash, Folder_vendor_details_PATH)
                    new_key = Folder_vendor_details_PATH+ csvSourceFilename
                    new_obj = new_bucket.Object(new_key)
                    logging.warn("obj.key::%s",filename)
                    logging.warn("new_key::%s",new_key)
                    print("File::::"+csvSourceFilename+":::copied into processedfiles/vendor_details/!!!!!!!!")
                    bucket = s3object.Bucket(DestinationBucketName)
                    objs = list(bucket.objects.filter(Prefix=Folder_vendor_details_PATH))
                    logging.warn("**************len(objs)*******vendor_details******** %s",len(objs))
                    for i in range(0, len(objs)):
                        logging.warn("%s",objs[i].key)
                        logging.warn("Before if condition::vendor_names::filename::::objs[i].key:::%s",objs[i].key)
                        if vendor_details in objs[i].key:
                            filename=objs[i].key
                            if filename.endswith("csv") and vendor_details in filename:
                                fileObj = client.get_object(Bucket =DestinationBucketName, Key=filename)
                                file_content = fileObj["Body"].read().decode('utf-8')

                                strfilecontent=str(file_content)
                                strfilecontentlist=strfilecontent.splitlines()
                                # logging.warn("strfilecontentlist::vendor_details:::%s",str(strfilecontentlist))
                                vendor_detailsRowCount=len(strfilecontentlist)
                                logging.warn("Number of Rows in file::vendor_details::%s",len(strfilecontentlist)) 
                                vendor_detailsRowCount=len(strfilecontentlist)
                                logging.warn("ActualFileRowCount::::%s",ActualFileRowCount)
                                logging.warn("vendor_detailsRowCount::::%s",vendor_detailsRowCount)
                                if ActualFileRowCount > vendor_detailsRowCount:
                                     logging.warn("I AM IN ActualFileRowCount > vendor_detailsRowCount:::::") 
                                     response = client.list_objects_v2(Bucket=DestinationBucketName, Prefix=Folder_vendor_details_PATH)
                                     for object in response['Contents']:
                                       logging.warn('Deleting: %s', object['Key'])
                                       if (vendor_details in object['Key']) and (object['Key'].endswith("csv")):
                                          client.delete_object(Bucket=DestinationBucketName, Key=object['Key'])
                                          print("File::::"+csvSourceFilename+":::Deleted into processedfiles/vendor_details/!!!!!!!!")
                                     
                                     new_obj.copy(old_source)
                                     logging.warn("obj.key::%s",filename)
                                     logging.warn("new_key::%s",new_key)
                                     print("File::::"+csvSourceFilename+":::copied into processedfiles/vendor_details/!!!!!!!!")     
                                else:
                                    logging.warn("Uploaded file No.Of ROW's is less then exsting File No.Of ROW's processedfiles/vendor_details/")
                            elif filename.endswith("csv"):
                                logging.warn("vendor_details csv File not found then copying NEW File:processedfiles/vendor_details/:::")
                                new_obj.copy(old_source)
                                logging.warn("obj.key::%s",filename)
                                logging.warn("new_key::%s",new_key)
                                print("File::::"+csvSourceFilename+":::copied into processedfiles/vendor_details/!!!!!!!!") 
                            
                            elif len(objs) == 1:
                                logging.warn("vendor_names csv file not found and len(objs) == 1 then copying new File::processedfiles/vendor_details/::::")
                                new_obj.copy(old_source)
                                logging.warn("obj.key::%s",filename)
                                logging.warn("new_key::%s",new_key)
                                print("File::::"+csvSourceFilename+":::copied into processedfiles/vendor_details/!!!!!!!!")    
        except ClientError as e:
              logging.warn("Copy ClientError::::%s",e)