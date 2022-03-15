import boto3
import json
import csv
import urllib
import boto3.session
import os
import time
import logging
import sys
from botocore.exceptions import ClientError

#from S3.Client.exceptions.NoSuchKey

s3 = boto3.client("s3")
s3_resource = boto3.resource('s3')
#s3 = boto3.resource('s3')

# adding variable so that the lambda is environment agnostic
environment = os.environ.get("ENVIRONMENT")

def lambda_handler(event, context):
    logger = logging.getLogger()
    logger.setLevel(logging.WARNING)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
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
    object_list_in_DestinationFolder=[]
    s3object = boto3.resource('s3')
    # Here we create a new session per thread
    session = boto3.session.Session()
    s3_resource = session.resource('s3')
    if event:
        logging.warn("Event :%s", event)
        time.sleep(20)
        new_bucket=""
        ActualFileRowCount=0
        vendor_detailsRowCount=0
        vendor_namesRowCount=0
        LenthOfObjectsInFile=0
        filenameLenghtcsv=0
        PropertiesFileTotalLists=[]
        filename=""
        mainSourceNamewithPath=''
        file_obj = event["Records"][0]
        bucket_name = str(file_obj['s3']['bucket']['name'])
        filename = str(file_obj['s3']['object']['key'])
        mainSourceNamewithPath=filename
        filenameLength=len(filename.split("/"))
        ##################################Property File Reading################################################
        properties_bucket_name=f"massgov-pfml-{environment}-redshift-daily-import"
        properties_filename="processedfiles/sharepoint/FileConfig/pfml_bi_file_load_config.csv"
        fromPropertyFile_FileName=""
        fromPropertyFile_Bucket=""
        fromPropertyFile_DestinationFolder=""
        fromPropertyFile_Is_Active=""
        fromPropertyFile_Refresh_Type=""
        propertiesfileObj = s3.get_object(Bucket =properties_bucket_name, Key=properties_filename)
        properties_file_content = propertiesfileObj["Body"].read().decode('utf-8')
        properties_strfilecontent=str(properties_file_content)
        properties_strfilecontentlist=properties_strfilecontent.splitlines()
        properties_strfilecontentlist.pop(0)
        logging.warn("properties_strfilecontentlist--Type:::::%s",type(properties_strfilecontentlist))
        for row in range(0,len(properties_strfilecontentlist)):
            FullRow=properties_strfilecontentlist[row]
            FullRowlines=FullRow.split(",")
            logging.warn("type(Properties-File-FullRowlines):::::::::%s",type(properties_strfilecontentlist))
            PropertiesFileTotalLists.append(FullRowlines)
            fromPropertyFile_FileName=FullRowlines[1]
            logging.warn("FileName::FromProperties:::::::%s",fromPropertyFile_FileName)
            fromPropertyFile_Bucket=FullRowlines[4]
            logging.warn("Bucket:::::FromProperties:::::::::::::%s",fromPropertyFile_Bucket)
            fromPropertyFile_DestinationFolder=FullRowlines[5]
            logging.warn("DestinationFolder:::::FromProperties::::::::::::%s",fromPropertyFile_DestinationFolder)
            fromPropertyFile_Is_Active=FullRowlines[7]
            logging.warn("Controller(Y/N):::::FromProperties::::::::::::::::::%s",fromPropertyFile_Is_Active)
            fromPropertyFile_Refresh_Type=FullRowlines[8]
            logging.warn("CopyType(FULL/INC):::::FromProperties:::::::::%s",fromPropertyFile_Refresh_Type)
        #######################################################################################################
            #Below code is for reading upload bucket,file information
            logging.warn("Event :: filenameLength::::::::::::%s",filenameLength)
            for i in range(filenameLength):
                filenameLenghtcsv=i
            logging.warn("Event Uploaded:: filename:::::%s",filename)
            csvSourceFilename=filename.split("/")[filenameLenghtcsv]
            csvSourceFolder=filename.split("/")[0]
            logging.warn("Event Uploaded::csvSourceFolder:::::%s",csvSourceFolder)
            logging.warn("Event Uploaded::bucket_name:::::%s",bucket_name)
            file_content=""
            try:
                new_bucket = s3_resource.Bucket(fromPropertyFile_Bucket )###^^^^
                fileObj = s3.get_object(Bucket =bucket_name, Key=filename)
                file_content = fileObj["Body"].read().decode('utf-8')
            except Exception as e:
                  logging.error('s3_resource.Bucket(fromPropertyFile_Bucket )&&&&s3.get_object :::::no such key in bucket')

            strfilecontent=str(file_content)
            strfilecontentlist=strfilecontent.splitlines()
            ActualFileRowCount=len(strfilecontentlist)
            logging.warn("Event Uploaded File contains Number of Rows in file length::::::%s",len(strfilecontentlist))
            EachRowCount.append(file_content)
            #logging.warn("Event Uploaded File::EachRowCount::::::::%s",EachRowCount)
            #Check if file exists in Process Folder
            #logging.warn("From Properties File:::Bucket Name:::::fromPropertyFile_Bucket::::::::%s",fromPropertyFile_Bucket)
            #logging.warn("From Properties File::fromPropertyFile_DestinationFolder:::::::::::::%s",fromPropertyFile_DestinationFolder)
            # destinationobject = s3.get_object(Bucket =fromPropertyFile_Bucket, Key=fromPropertyFile_FileName+'/'+fromPropertyFile_FileName)
            try:
                  #bucket = s3_resource.Bucket(fromPropertyFile_Bucket)
                  object_listing = s3.list_objects_v2(Bucket=fromPropertyFile_Bucket,
                                    Prefix=fromPropertyFile_DestinationFolder+'/')
            except Exception as e:
                  logging.error("s3.list_objects_v2(Bucket=fromPropertyFile_Bucket,Prefix=fromPropertyFile_DestinationFolder+/) :::::no such key in bucket!!!!!")
            #Below code is for Objects exists in Destination bucket and folder
            if "Contents" in object_listing:
               for object in object_listing['Contents']:
                 logging.warn("Files found in folder::$$$$::::::::%s",object['Key'])
                 object_list_in_DestinationFolder.append(object['Key'].split("/")[2])
                 logging.warn("Files found in folder::$$$$::::::::%s",object['Key'].split("/")[2])
            else:
                 logging.warn("No Files found in Folder:response[Contents]::$$$$%%%%%%%% :::::no such key in bucket!!!!!",object_listing)
            objs = object_list_in_DestinationFolder
            EventUploadedFile=fromPropertyFile_FileName
            element_in_sublists = [EventUploadedFile in list for list in PropertiesFileTotalLists]
            logging.warn("element_in_sublists:::::::%s",element_in_sublists)
            PropertiesFile_in_lists = any(element_in_sublists)
            logging.warn("PropertiesFile_in_lists::::$$$$$$$$$$$$:::%s",PropertiesFile_in_lists)
            logging.warn("objs::******************$$$$$$$$$$$::::::***:%s",objs)
            logging.warn("len(objs)::******************$$$$$$$$$$$::::::***:%s",len(objs))
            #logging.warn("Event Uploaded::csvSourceFilename::::::%s",csvSourceFilename)
            #logging.warn("fromPropertyFile_FileName::::::%s",fromPropertyFile_FileName)
            if ((PropertiesFile_in_lists == True) and (fromPropertyFile_FileName in csvSourceFilename)):
                logging.warn("Uploaded Files existed in properties destination Folder :::::key exists!!:::::::***:%s")
                if ((fromPropertyFile_Is_Active == 'Y') and (fromPropertyFile_Refresh_Type == "FULL") ):
                    logging.warn("From Properties File:::::fromPropertyFile_Is_Active::::***:%s",fromPropertyFile_Is_Active)
                    try:
                        #time.sleep(5)
                        if(len(objs)>0 and csvSourceFilename.endswith('.csv')) :##T^^^^his condition for Checking file exists or not
                        #if(("Contents" in objs) and (csvSourceFilename.endswith('.csv'))) :
                            logging.warn("Event Uploaded::::bucket_name::^^^^%%%%$$$$$$::::::***:%s",bucket_name)
                            logging.warn("Event Uploaded File Name::csvSourceFilename::::::::***:%s",csvSourceFilename)
                            csvSourceFolderwithSlash=csvSourceFolder+"/"
                            old_source = { 'Bucket': bucket_name,
                                      'Key': csvSourceFilename}

                            #logging.warn("Event Uploaded::::old_source:::^^^%%%%$$$$:::::***:%s",old_source)
                            #logging.warn("Event Uploaded::::csvSourceFolderwithSlash::::::::***:%s",csvSourceFolderwithSlash)
                            #logging.warn("From Properties File::fromPropertyFile_DestinationFolder::::::::***:%s",fromPropertyFile_DestinationFolder)
                            new_key = filename.replace(csvSourceFolderwithSlash, fromPropertyFile_DestinationFolder)
                            new_key = fromPropertyFile_DestinationFolder+"/"+ csvSourceFilename
                            new_obj = new_bucket.Object(new_key)
                            #logging.warn("Event Uploaded:::File Name:::obj.key::::::::::::***:%s",csvSourceFilename)
                            #logging.warn("Destination Folder+File path::::new_key::::::::::::***:%s",new_key)
                            bucket = s3object.Bucket(fromPropertyFile_Bucket)
                            objs = list(bucket.objects.filter(Prefix=fromPropertyFile_DestinationFolder))
                            logging.warn("**************len(objs)***************::::::::::::***:%s",len(objs))
                            for i in range(0, len(objs)):
                             logging.warn("objs[i].key::filename::::::::::::***:%s",objs[i].key)
                             if fromPropertyFile_FileName in objs[i].key:
                                 filename=objs[i].key
                                 logging.warn("Before if condition::::filename::::::::::::***:%s",filename)
                                 if filename.endswith("csv") and fromPropertyFile_FileName in filename:#need to review this condition
                                     fileObj = client.get_object(Bucket =fromPropertyFile_Bucket, Key=filename)
                                     file_content = fileObj["Body"].read().decode('utf-8')
                                 #    logging.warn("Event Uploaded::::file_content::::::::::::***:%s",str(file_content))
                                     strfilecontent=str(file_content)
                                     strfilecontentlist=strfilecontent.splitlines()
                                     #logging.warn("Event Uploaded:::strfilecontentlist:::::::::::::::::***:%s",str(strfilecontentlist))
                                     #Uploaed File length=len(strfilecontentlist)
                                     Uploaded_File_RowCount=len(strfilecontentlist)
                                     #logging.warn("Event Uploaded::::Number of Rows in file:::::::::::::::::***:%s",len(strfilecontentlist))
                                     logging.warn("Event Uploaded::::ActualFileRowCount:::::::::::::::::***:%s",ActualFileRowCount)
                                     logging.warn("Uploaded_File_RowCount:::::::::::::::::***:%s",Uploaded_File_RowCount)
                                     if fromPropertyFile_Refresh_Type == "FULL":
                                         logging.warn("fromPropertyFile_Refresh_Type == FULL then compare the new file count with old file count:***:%s")
                                         if ActualFileRowCount >= Uploaded_File_RowCount:
                                             #If New file Number of Row's is greater then old file then copy the New file
                                             logging.warn("I AM IN ActualFileRowCount > Uploaded_File_RowCount:***:%s")
                                             response = client.list_objects_v2(Bucket=fromPropertyFile_Bucket, Prefix=fromPropertyFile_DestinationFolder)
                                             #logging.warn("response**in fromPropertyFile_Refresh_Type =FULL***/:*:%s",response)
                                             for object in response['Contents']:
                                               logging.warn("Deleting:***:%s",object['Key'])
                                               #bucket = s3_resource.Bucket(fromPropertyFile_Bucket)
                                               #bucket.objects.filter(Prefix=fromPropertyFile_DestinationFolder).delete()
                                               client.delete_object(Bucket=fromPropertyFile_Bucket, Key=object['Key'])
                                               logging.warn("File::::%s"+object['Key']+":::Deleted previous file processedfiles/*****/!!!!!!!!:***:%s")
                                             old_source = { 'Bucket': bucket_name,'Key': mainSourceNamewithPath}
                                             new_key = filename.replace(csvSourceFolderwithSlash, fromPropertyFile_DestinationFolder)
                                             new_key = fromPropertyFile_DestinationFolder+"/"+ csvSourceFilename
                                             logging.warn("Destination Folder+File path:::::new_key::::***:%s",new_key)
                                             new_obj = new_bucket.Object(new_key)
                                             #logging.warn("Event Uploaded:: :::new_obj::::***:%s",new_obj)
                                             #logging.warn("Befoer Copy Object if Greater Then File:::::::***:%s")
                                             #new_obj.copy(old_source)
                                             s3_resource.meta.client.copy(old_source, fromPropertyFile_Bucket, new_key)
                                             logging.warn("After Copy Object if Greater Then File:::::::***:%s")
                                             result="Successfull."
                                             emailsend(csvSourceFilename,result)
                                             logging.warn("After Copy&&&Uploaded File &&&&& email sent::***:%s")
                                             logging.warn("File::::%s"+csvSourceFilename+":::copied into processedfiles/VBI_**********/!!!!!!!!:***:%s")

                                         else:
                                             logging.warn("Event Uploaded::::ActualFileRowCount:::::::::::::::::***:%s",ActualFileRowCount)
                                             logging.warn("Uploaded_File_RowCount:::::::::::::::::***:%s",Uploaded_File_RowCount)
                                             result="Faild because of less record count."
                                             emailsend(csvSourceFilename,result)
                                             logging.warn("Event Uploaded:: file::ActualFileRowCount is less then processedfiles/VBI_*****/Destnation Row Count::::::::***:%s")

                        #This code is for uploaded file not found
                        elif ((len(objs) == 0)):###^^^^
                        #elif ("Contents" not in  objs):
                          logging.warn("key doesn't exist!::len(objs) == 0::***:%s",len(objs))
                          response = client.list_objects_v2(Bucket=fromPropertyFile_Bucket, Prefix=fromPropertyFile_DestinationFolder)
                          #logging.warn("response**in fromPropertyFile_Refresh_Type =FULL*$$$$$$$$$$$$**/:*:%s",response)
                          csvSourceFolderwithSlash=csvSourceFolder+"/"
                          old_source = { 'Bucket': bucket_name,
                                      'Key': filename}
                          #elif len(objs) == 1:##Need to review this condition
                          #logging.warn("Event Uploaded:: filename file not found and len(objs) == 1 then copying new File::processedfiles/VBI_*****/:*:%s")
                          #logging.warn("Event Uploaded::::csvSourceFolderwithSlash:*****/:*:%s",csvSourceFolderwithSlash)
                          #logging.warn("From Properties File::fromPropertyFile_DestinationFolder*****/:*:%s",fromPropertyFile_DestinationFolder)
                          new_key = filename.replace(csvSourceFolderwithSlash, fromPropertyFile_DestinationFolder)
                          new_key = fromPropertyFile_DestinationFolder+"/"+ csvSourceFilename
                          new_obj = new_bucket.Object(new_key)
                          new_obj.copy(old_source)
                          result="Successfull."
                          emailsend(csvSourceFilename,result)
                          logging.warn("Email sent &&& Copied File into processedfiles/VBI_*****/!!!!!!!!***csvSourceFilename**/:*:%s",csvSourceFilename)
                          # new_obj.copy(old_source)
                          logging.warn("Event Uploaded:::File Name:::obj.key:::*:%s",filename)
                          logging.warn("Destination Folder+File path::::new_key:::::*:%s",new_key)

                    except ClientError as e:
                          logging.error("s3_resource.Bucket(fromPropertyFile_Bucket) :::::no such key in bucket!!!!!..%s",e)
                #############################Flag=Y and RefreshType is  INC###############################

                elif ((fromPropertyFile_Is_Active == 'Y') and (fromPropertyFile_Refresh_Type == "INC") ):
                    logging.warn("IN Condition ::::fromPropertyFile_Is_Active == 'Y') and (fromPropertyFile_Refresh_Type == INC::::::::::::::::*:%s")
                    logging.warn("From Properties File:::::fromPropertyFile_Is_Active:::::::::::::::::::*:%s",fromPropertyFile_Is_Active)
                    logging.warn("From Properties File:::::fromPropertyFile_Refresh_Type:::::::::::::::::::*:%s",fromPropertyFile_Refresh_Type)

                    try:
                        #time.sleep(5)
                        if(len(objs)>0 and filename.endswith('.csv')) :
                            csvSourceFolderwithSlash=csvSourceFolder+"/"
                            if filename.endswith('.csv'):
                                old_source = { 'Bucket': bucket_name,
                                          'Key': filename}

                                if  fromPropertyFile_FileName in filename: #Enhance with Properties files
                                    new_key = filename.replace(csvSourceFolderwithSlash, fromPropertyFile_DestinationFolder)
                                    new_key = fromPropertyFile_DestinationFolder+"/"+ csvSourceFilename
                                    new_obj = new_bucket.Object(new_key)
                                    # new_obj.copy(old_source)
                                    logging.warn("Event Uploaded:::File Name:::obj.key:::::::::::::::::::*:%s",filename)
                                    logging.warn("Destination Folder+File path::::new_key::::::::::::::::::::*:%s",new_key)
                                    # print("File::::"+csvSourceFilename+":::copied into processedfiles/vendor_names/!!!!!!!!")
                                    bucket = s3object.Bucket(fromPropertyFile_Bucket)
                                    objs = list(bucket.objects.filter(Prefix=fromPropertyFile_DestinationFolder))
                                    logging.warn("**************len(objs)***************::::::::::::::::::::*:%s",len(objs))
                                    for i in range(0, len(objs)):
                                        logging.warn("objs[i].key::filename:::::::::::::::*:%s",objs[i].key)
                                        if fromPropertyFile_FileName in objs[i].key:
                                            filename=objs[i].key
                                            logging.warn("Before if condition::vendor_names::filename:::::::::::::::*:%s",filename)
                                            #If CSV File not exists then Copying the new file
                                            logging.warn("fromPropertyFile_Refresh_Type == INC then copying new File::processedfiles/VBI_*****/::::::::*:%s")
                                            new_obj.copy(old_source)
                                            result="Successfull."
                                            emailsend(csvSourceFilename,result)
                                            logging.warn("Email sent_Event Uploaded:: filename:::obj.key:*****/::::::::*:%s",csvSourceFilename)
                                            logging.warn("Destination Folder+File path::::new_key:*****/::::::::*:%s",new_key)

                        #This code is for uploaded file not found
                        elif (len(objs) == 0):
                          logging.warn("key doesn't exist!:*****/:::len(objs) == 0:::::*:%s")
                          csvSourceFolderwithSlash=csvSourceFolder+"/"
                          old_source = { 'Bucket': bucket_name,
                                      'Key': filename}
                          new_key = filename.replace(csvSourceFolderwithSlash, fromPropertyFile_DestinationFolder)
                          new_key = fromPropertyFile_DestinationFolder+"/"+ csvSourceFilename
                          new_obj = new_bucket.Object(new_key)
                          new_obj.copy(old_source)
                          result="Successfull."
                          emailsend(csvSourceFilename,result)
                          # new_obj.copy(old_source)
                          logging.warn("Email sent_Event Uploaded:: filename:::obj.key:*****/:copied into processedfiles/VBI_*****/!!!!!!!!:::::::*:%s",filename)
                          logging.warn("Destination Folder+File path::::new_key:*****/::::::::*:%s",new_key)

                    except ClientError as e:
                          logging.error("Copy Error :::::no such key in bucket!!!!!..%s",e)
                ###################################################r#######################################

                elif fromPropertyFile_Is_Active == 'N':
                         logging.warn("Is_Active is N:::::::*****:%s",fromPropertyFile_Is_Active)


            else:
                 logging.warn("Uploaded file not found in  properties file:::processedfiles/VBI:*****:%s",)

def emailsend(filename,result):
    #############################################Email########################################################

    # Replace sender@example.com with your "From" address.
    # This address must be verified with Amazon SES.
    SENDER = "ravitejatella@gmail.com"

    # Replace recipient@example.com with a "To" address. If your account
    # is still in the sandbox, this address must be verified.
    RECIPIENT = "ravitejatella@gmail.com"

    # Specify a configuration set. If you do not want to use a configuration
    # set, comment the following variable, and the
    # ConfigurationSetName=CONFIGURATION_SET argument below.
    CONFIGURATION_SET = "ConfigSet"

    # If necessary, replace us-west-2 with the AWS Region you're using for Amazon SES.
    AWS_REGION = "us-east-1"

    # The subject line for the email.
    SUBJECT = "AWS Cloud S3 Bucket:redshiftbidailyloads Daily uploaded Files"
    value=420
    # The email body for recipients with non-HTML email clients.
    BODY_TEXT = ("AWS Cloud S3 Bucket:redshiftbidailyloads Daily uploaded Files\r\n"
                 "Today's files has been uploaded into AWS Cloud S3 Bucket:redshiftbidailyloads "
                 )
    #####################################################################################################

    value=filename

    # The HTML body of the email.
    BODY_HTML = """<html>
    <head></head>
    <body>
      <h1>Amazon S3 Files Uploaded information</h1>
      <p>AWS Cloud S3 Bucket:redshiftbidailyloads Daily uploaded File
          """+str(value)+""" has been uploaded::+"""+ str(result) +"""</p>
    </body>
    </html>
                """

    # The character encoding for the email.
    CHARSET = "UTF-8"

    # Create a new SES resource and specify a region.
    client = boto3.client('ses',region_name=AWS_REGION)

    # Try to send the email.
    try:
        #Provide the contents of the email.
        response = client.send_email(
            Destination={
                'ToAddresses': [
                    RECIPIENT,
                ],
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': CHARSET,
                        'Data': BODY_HTML,
                    },
                    'Text': {
                        'Charset': CHARSET,
                        'Data': BODY_TEXT,
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': SUBJECT,
                },
            },
            Source=SENDER,
            # If you are not using a configuration set, comment or delete the
            # following line
            #ConfigurationSetName=CONFIGURATION_SET,
        )
    # Display an error if something goes wrong.
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])