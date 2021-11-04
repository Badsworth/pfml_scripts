import boto3
import json
import csv
import urllib
import boto3.session
import time
from botocore.exceptions import ClientError

s3 = boto3.client("s3")
s3_resource = boto3.resource('s3')
#s3 = boto3.resource('s3')


def __main__(event, context):

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
    DestinationBucketName="massgov-pfml-stage-redshift-daily-import"
    s3object = boto3.resource('s3')
    # Here we create a new session per thread
    session = boto3.session.Session()
    s3_resource = session.resource('s3')
    if event:
        print("Event :", event)
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
        print("filenameLength::::",filenameLength)
        for i in range(filenameLength):
            filenameLenghtcsv=i
        print("filename::::",filename)
        csvSourceFilename=filename.split("/")[filenameLenghtcsv]
        csvSourceFolder=filename.split("/")[0]
        print("csvSourceFolder :", csvSourceFolder)
        print("csvSourceFilename :", csvSourceFilename)
        print("bucket_name :", bucket_name)
        old_bucket = s3_resource.Bucket(bucket_name )
        new_bucket = s3_resource.Bucket(DestinationBucketName )
        fileObj = s3.get_object(Bucket =bucket_name, Key=filename)
        file_content = fileObj["Body"].read().decode('utf-8')
        #print("file_content::::",file_content)
        #print("Final Output::::",file_content)
        #print("filecontent:::",str(file_content))
        strfilecontent=str(file_content)
        strfilecontentlist=strfilecontent.splitlines()
        #print("strfilecontentlist:::::",str(strfilecontentlist))
        ActualFileRowCount=len(strfilecontentlist)
        print("Number of Rows in file::::",len(strfilecontentlist))
        # file = open(csvFilename)
        # reader = csv.reader(file)
        # lines= len(list(reader))

        # print("Number of row in File::::::",lines)
        EachRowCount.append(file_content)
        print("EachRowCount::",EachRowCount)
        #Check if file exists in Process Folder
        
        result_vendor_details = s3.list_objects(Bucket = DestinationBucketName, Prefix=processedfiles_vendor_details)
        folderandfilesLength=result_vendor_details.get("Contents")
        print("Lenghof Contents::::result_vendor_details:::::",len(folderandfilesLength))
        print("Contents::::result_vendor_details::",folderandfilesLength)
        #if len(folderandfilesLength) > 1:
        print("len(folderandfilesLength):::LENGTH OF Destination Folder:::result_vendor_details:::",len(folderandfilesLength))
            #for j in range(1,len(folderandfilesLength)):
                #for i in folderandfilesLength:
                #print("JJJJJJJJJJJJ Value:::result_vendor_details::",j)
        print("Source Contents for File:::result_vendor_details::",folderandfilesLength[0].get("Key"))
        #print("IIIIIIIIIIIIIresult_vendor_detailsIIIII",folderandfilesLength[0])
        Folder_vendor_details_PATH=folderandfilesLength[0].get("Key")
        print("Source Files======folderandfilesLength[1].get(Key)===>:result_vendor_details:::::",Folder_vendor_details_PATH)
        if not Folder_vendor_details_PATH.endswith("csv"):
           print("Folder_vendor_details::::::result_vendor_details:::::::",Folder_vendor_details_PATH)
           DestinationPATHList.append(Folder_vendor_details_PATH)
           #csvDestinationPATH=Files
                    # FolderandFile=folderandfilesLength[j].get("Key").split("/")
                    # FolderandFileLength=len(FolderandFile)
                    # folder=FolderandFile[0]
                    # csvDestinationFile=FolderandFile[1]
                    # print("Source FolderandFileLength:::",FolderandFileLength)
                    # print("Source Folder:::",folder)
                    # print("Source File:::",csvDestinationFile)
        result_vendor_names = s3.list_objects(Bucket = DestinationBucketName, Prefix=processedfiles_vendor_names)
        folderandfilesLength=result_vendor_names.get("Contents")
        print("Lenghof Contents::_vendor_names:::",len(folderandfilesLength))
        print("Contents:::_vendor_names:::",folderandfilesLength)
        #if len(folderandfilesLength) > 1:
        print("len(folderandfilesLength):::LENGTH OF Destination Folder::_vendor_names:::::",len(folderandfilesLength))
            #for j in range(1,len(folderandfilesLength)):
                #for i in folderandfilesLength:
                #print("JJJJJJJJJJJJ Value:::_vendor_names::",j)
        print("Source Contents for File:::_vendor_names:::",folderandfilesLength[0].get("Key"))
        print("IIIIIIIIIIIIIIII_vendor_namesII",folderandfilesLength[0])
        Folder_vendor_names_PATH=folderandfilesLength[0].get("Key")
        print("Source Folder_vendor_names======folderandfilesLength[1].get(Key)===>:::::_vendor_names:::",Folder_vendor_names_PATH)
        if not Folder_vendor_names_PATH.endswith("csv"):
           print("Folder_vendor_names::::::::_vendor_names:::::",Folder_vendor_names_PATH)
           DestinationPATHList.append(Folder_vendor_names_PATH)
        #if ("vendor_details" in csvSourceFilename and "vendor_details" in Folder_vendor_details_PATH): 
        copy_source = {
                      'Bucket': bucket_name,
                      'Key': csvSourceFilename
                     }
        print("bucket_name:::",bucket_name)#old Bucket
        print("Source File Name::",filename)#obj.key
        print("csvSourceFilename::::",csvSourceFilename)#old file name
        print("Distination Path::Folder_vendor_details_PATH:::::",Folder_vendor_details_PATH)
        print("Distination Path::Folder_vendor_names_PATH:::::",Folder_vendor_names_PATH)
        try:
            #time.sleep(5)
            csvSourceFolderwithSlash=csvSourceFolder+"/"
            if filename.endswith('.csv'):
                old_source = { 'Bucket': bucket_name,
                           'Key': filename}
                 
                if  vendor_names in filename:
                    print("In vendor_names:::::::::::::::")
                    # replace the prefix
                    print("vendor_names csv file not found then copying new File:::")
                    print("csvSourceFolderwithSlash::::",csvSourceFolderwithSlash)
                    print("Folder_vendor_names_PATH:::",Folder_vendor_names_PATH)
                    new_key = filename.replace(csvSourceFolderwithSlash, Folder_vendor_names_PATH)
                    new_key = Folder_vendor_names_PATH+ csvSourceFilename
                    new_obj = new_bucket.Object(new_key)
                    # new_obj.copy(old_source)
                    print("obj.key::",filename)
                    print("new_key::",new_key)
                    # print("File::::"+csvSourceFilename+":::copied into processedfiles/vendor_names/!!!!!!!!")
                    bucket = s3object.Bucket(DestinationBucketName)
                    objs = list(bucket.objects.filter(Prefix=Folder_vendor_names_PATH))
                    print("**************len(objs)***vendor_names************",len(objs))
                    for i in range(0, len(objs)):
                        print(objs[i].key)
                        print("objs[i].key::filename:::",objs[i].key)
                        if vendor_names in objs[i].key:
                            filename=objs[i].key
                            print("Before if condition::vendor_names::filename:",filename)
                            if filename.endswith("csv") and vendor_names in filename:
                                fileObj = client.get_object(Bucket =DestinationBucketName, Key=filename)
                                file_content = fileObj["Body"].read().decode('utf-8')
                                print("file_content:vendor_names:::",file_content)
                                print("Final Output:vendor_names:::",file_content)
                                print("filecontent:vendor_names::",str(file_content))
                                strfilecontent=str(file_content)
                                strfilecontentlist=strfilecontent.splitlines()
                                print("strfilecontentlist::vendor_names:::",str(strfilecontentlist))
                                vendor_namesRowCount=len(strfilecontentlist)
                                print("Number of Rows in file::vendor_names::",len(strfilecontentlist))
                                vendor_namesRowCount=len(strfilecontentlist)
                                print("ActualFileRowCount::::",ActualFileRowCount)
                                print("vendor_detailsRowCount::::",vendor_namesRowCount)
                                if ActualFileRowCount > vendor_namesRowCount:
                                    #If New file Number of Row's is greater then old file then copy the New file  
                                    print("I AM IN ActualFileRowCount > vendor_namesRowCount")
                                    #print("csvSourceFolderwithSlash::::",csvSourceFolderwithSlash)
                                    #print("Folder_vendor_names_PATH:::",Folder_vendor_names_PATH)
                                    #new_key = filename.replace(csvSourceFolderwithSlash, Folder_vendor_names_PATH)
                                    #new_obj = new_bucket.Object(new_key)
                                    response = client.list_objects_v2(Bucket=DestinationBucketName, Prefix=Folder_vendor_names_PATH)
                                    for object in response['Contents']:
                                      print('Deleting', object['Key'])
                                      if (vendor_names in object['Key']) and object['Key'].endswith("csv"):
                                         client.delete_object(Bucket=DestinationBucketName, Key=object['Key'])
                                         print("File::::"+csvSourceFilename+":::Deleted into processedfiles/vendor_names/!!!!!!!!")
                                    new_obj.copy(old_source)
                                    print("obj.key::",filename)
                                    print("new_key::",new_key)
                                    print("File::::"+csvSourceFilename+":::copied into processedfiles/vendor_names/!!!!!!!!")
                                else:
                                    print("vendor_details csv File not found then copying NEW File:processedfiles/vendor_names/:::")
                            elif filename.endswith("csv"):
                                #If CSV File not exists then Copying the new file
                                print("vendor_names csv file not found then copying new File::processedfiles/vendor_names/::::")
                                #print("csvSourceFolderwithSlash::::",csvSourceFolderwithSlash)
                                #print("Folder_vendor_names_PATH:::",Folder_vendor_names_PATH)
                                #new_key = filename.replace(csvSourceFolderwithSlash, Folder_vendor_names_PATH)
                                #new_obj = new_bucket.Object(new_key)
                                new_obj.copy(old_source)
                                print("obj.key::",filename)
                                print("new_key::",new_key)
                                print("File::::"+csvSourceFilename+":::copied into processedfiles/vendor_names/!!!!!!!!")
                            
                            elif len(objs) == 1:
                                print("vendor_names csv file not found and len(objs) == 1 then copying new File::processedfiles/vendor_names/::::")
                                #print("csvSourceFolderwithSlash::::",csvSourceFolderwithSlash)
                                #print("Folder_vendor_names_PATH:::",Folder_vendor_names_PATH)
                                #new_key = filename.replace(csvSourceFolderwithSlash, Folder_vendor_names_PATH)
                                #new_obj = new_bucket.Object(new_key)
                                new_obj.copy(old_source)
                                print("obj.key::",filename)
                                print("new_key::",new_key)
                                print("File::::"+csvSourceFilename+":::copied into processedfiles/vendor_names/!!!!!!!!")
                                
                elif vendor_details in filename:
                    print("In vendor_details:::::::::::::::")
                    #replace the prefix
                    print("vendor_details csv File not found then copying NEW File::::")
                    print("csvSourceFolderwithSlash::::",csvSourceFolderwithSlash)
                    print("Folder_vendor_details_PATH:::",Folder_vendor_details_PATH)
                    new_key = filename.replace(csvSourceFolderwithSlash, Folder_vendor_details_PATH)
                    new_key = Folder_vendor_details_PATH+ csvSourceFilename
                    new_obj = new_bucket.Object(new_key)
                    #new_obj.copy(old_source)
                    print("obj.key::",filename)
                    print("new_key::",new_key)
                    print("File::::"+csvSourceFilename+":::copied into processedfiles/vendor_details/!!!!!!!!")
                    bucket = s3object.Bucket(DestinationBucketName)
                    objs = list(bucket.objects.filter(Prefix=Folder_vendor_details_PATH))
                    print("**************len(objs)*******vendor_details********",len(objs))
                    for i in range(0, len(objs)):
                        print(objs[i].key)
                        print("Before if condition::vendor_names::filename::::objs[i].key:::",objs[i].key)
                        if vendor_details in objs[i].key:
                            filename=objs[i].key
                            if filename.endswith("csv") and vendor_details in filename:
                                fileObj = client.get_object(Bucket =DestinationBucketName, Key=filename)
                                file_content = fileObj["Body"].read().decode('utf-8')
                                print("file_content:vendor_details:::",file_content)
                                print("Final Output:vendor_details:::",file_content)
                                print("filecontent:vendor_details::",str(file_content))
                                strfilecontent=str(file_content)
                                strfilecontentlist=strfilecontent.splitlines()
                                print("strfilecontentlist::vendor_details:::",str(strfilecontentlist))
                                vendor_detailsRowCount=len(strfilecontentlist)
                                print("Number of Rows in file::vendor_details::",len(strfilecontentlist)) 
                                vendor_detailsRowCount=len(strfilecontentlist)
                                print("ActualFileRowCount::::",ActualFileRowCount)
                                print("vendor_detailsRowCount::::",vendor_detailsRowCount)
                                if ActualFileRowCount > vendor_detailsRowCount:
                                     print("I AM IN ActualFileRowCount > vendor_detailsRowCount:::::") 
                                     #print("csvSourceFolderwithSlash::::",csvSourceFolderwithSlash)
                                     #print("Folder_vendor_names_PATH:::",Folder_vendor_names_PATH)
                                     #new_key = filename.replace(csvSourceFolderwithSlash, Folder_vendor_details_PATH)
                                     #new_obj = new_bucket.Object(new_key)
                                     response = client.list_objects_v2(Bucket=DestinationBucketName, Prefix=Folder_vendor_details_PATH)
                                     for object in response['Contents']:
                                       print('Deleting', object['Key'])
                                       if (vendor_details in object['Key']) and (object['Key'].endswith("csv")):
                                          client.delete_object(Bucket=DestinationBucketName, Key=object['Key'])
                                          print("File::::"+csvSourceFilename+":::Deleted into processedfiles/vendor_details/!!!!!!!!")
                                     
                                     new_obj.copy(old_source)
                                     print("obj.key::",filename)
                                     print("new_key::",new_key)
                                     print("File::::"+csvSourceFilename+":::copied into processedfiles/vendor_details/!!!!!!!!")     
                                else:
                                    print("Uploaded file No.Of ROW's is less then exsting File No.Of ROW's processedfiles/vendor_details/")
                            elif filename.endswith("csv"):
                                print("vendor_details csv File not found then copying NEW File:processedfiles/vendor_details/:::")
                                #print("csvSourceFolderwithSlash::::",csvSourceFolderwithSlash)
                                #print("Folder_vendor_names_PATH:::",Folder_vendor_names_PATH)
                                #new_key = filename.replace(csvSourceFolderwithSlash, Folder_vendor_details_PATH)
                                #new_obj = new_bucket.Object(new_key)
                                new_obj.copy(old_source)
                                print("obj.key::",filename)
                                print("new_key::",new_key)
                                print("File::::"+csvSourceFilename+":::copied into processedfiles/vendor_details/!!!!!!!!") 
                            
                            elif len(objs) == 1:
                                print("vendor_names csv file not found and len(objs) == 1 then copying new File::processedfiles/vendor_details/::::")
                                #print("csvSourceFolderwithSlash::::",csvSourceFolderwithSlash)
                                #print("Folder_vendor_names_PATH:::",Folder_vendor_names_PATH)
                                #new_key = filename.replace(csvSourceFolderwithSlash, Folder_vendor_names_PATH)
                                #new_obj = new_bucket.Object(new_key)
                                new_obj.copy(old_source)
                                print("obj.key::",filename)
                                print("new_key::",new_key)
                                print("File::::"+csvSourceFilename+":::copied into processedfiles/vendor_details/!!!!!!!!")    
        except ClientError as e:
              print("Copy ClientError::::",e)