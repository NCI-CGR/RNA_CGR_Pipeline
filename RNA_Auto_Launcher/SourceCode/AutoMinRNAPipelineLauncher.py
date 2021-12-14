'''
Purpose: 
Auto-trigger mini RNA pipeline  
 
Input:
Flowcell data folder

Output:
New Flowcell List ->

'''
import sys
import os
import subprocess

#LOGDir = "/home/lixin/lxwg/Data/Log"
LOGDir = "/DCEG/Projects/Exome/SequencingData/DAATeam/Log/RNAPipeline" 

HISEQLogDir   = LOGDir + "/HiSeq"
MISEQLogDir   = LOGDir + "/MiSeq"
NEXTSEQLogDir = LOGDir + "/NextSeq"
OTHERLogDir   = LOGDir + "/Other"

DONEFlagEmail = "flag_email_sent_done"
DONEFlagWarningEmail = "flag_email_warning_sent_done"
DONEFlagRNA = "RNA.QC.Complete"
WORKINGFlagRNA = "RNA.QC.Running"

RNAPipelineFolder = "LIMS_RNA_Pipeline"
RNAWorkingList = "Working_list.txt"
RNADoneList = "Done_list.txt"

DICDataType = {"RNA"  : 0,
               "Other": 1}

EMAILSender = "xin.li4@nih.gov"

# EMAILReceiverEnd = "xin.li4@nih.gov"
# EMAILReceiverWarning = "xin.li4@nih.gov"
# EMAILReceiverStart = "xin.li4@nih.gov"

#EMAILReceiverEnd = "mia.steinberg@nih.gov,amulya.shastry@nih.gov,xin.li4@nih.gov,bin.zhu2@nih.gov,kristine.jones@nih.gov,russell.williams@nih.gov"
#EMAILReceiverWarning = "mia.steinberg@nih.gov,amulya.shastry@nih.gov,xin.li4@nih.gov,bin.zhu2@nih.gov" 
#EMAILReceiverStart = "mia.steinberg@nih.gov,amulya.shastry@nih.gov,xin.li4@nih.gov,bin.zhu2@nih.gov,kristine.jones@nih.gov,russell.williams@nih.gov"
EMAILReceiverEnd = "xin.li4@nih.gov,kristine.jones@nih.gov,herbert.higson@nih.gov,elizabeth.leumas@nih.gov,chowdhsa@mail.nih.gov"
EMAILReceiverWarning = "xin.li4@nih.gov"
EMAILReceiverStart = "xin.li4@nih.gov,kristine.jones@nih.gov,herbert.higson@nih.gov,elizabeth.leumas@nih.gov,chowdhsa@mail.nih.gov"

SUBMITScript = "/DCEG/Projects/Exome/SequencingData/DAATeam/RNAPipeline/Mia/Submit.sh"

RNAQCRepoDirName = "LIMS_RNA_Pipeline" 
RNAQCRepoURL = "git@10.133.130.114:lxwgcool/LIMS_RNA_Pipeline.git"
RNAQCRepoHPC = "/DCEG/Projects/Exome/SequencingData/DAATeam/RNAPipeline/LIMS_RNA_Pipeline"

DROPBOXDir = "/DCEG/CGF/Laboratory/LIMS/drop-box-prod/RNAsequenceqc"

ERRORMsg = "Exiting because a job execution failed"
MAXNoUpdateHours = 5

class ClsFlowcell:
    def __init__(self):
        self.strCaptureKit = ""
        self.iDataType = DICDataType["Other"]         
        
        self.bPrimaryDone = False
        self.bRNADone = False
        self.bRNANew = False
        self.bRNAEmailSent = False
        # to control the error -->
        # Case 1
        self.bAbnomralFlag = False
        # Case 2
        self.bMissingDir = False
        self.strMissingDir = ""
        # Case 3
        self.bErrorMsg = False
        self.strErrorLog = ""
        # Case 4
        self.bAbnormalJob = False
        self.strZombieLog = ""
        # <--
        
        self.strPlatform = "Other"
        self.strRunID = ""
        self.strRootDir = ""
        self.strLogDir = ""
        
    def Init(self, strDir):
        #1: Check if it is RNA or DNA --> Go!!
        #(1) Get Samplesheet
        CMD = "find " + strDir + " -maxdepth 1 -iname \"*.csv\""        
        #print("CMD:", CMD)
        strSampleSheet = subprocess.getoutput(CMD).split("\n")[0]
        #print("strSampleSheet", strSampleSheet)
        
        #(2) Get CaptureKit ->
        CMD = ("cat " + strSampleSheet + 
               " |  grep -i \"CaptureKit\"" + 
               " | awk -F ';' '{for(i=1;i<=NF;i++){if ($i ~ \"CaptureKit\"){print $i}}}'" + 
               " | head -n 1 | awk -F '=' '{print $2}'")
        #print("CMD:", CMD)
        strCaptureKit = subprocess.getoutput(CMD)
        self.strCaptureKit = strCaptureKit 
        #print("strCaptureKit", strCaptureKit)
        
        # Get Data Type        
        if "RNA" in strCaptureKit:
            self.iDataType = DICDataType["RNA"]
            
        # Get PlatForm
        self.strPlatform = strDir.split('/')[-4]
        
        # Get Primary Flag
        # For old flag
        bAllDoneFlagOld = os.path.exists(strDir + "/flag_all_analysis_done")
        
        # For new flag
        bAllDoneFlagNew = False
        strFlagNewDir = strDir + "/Flag"
        if os.path.exists(strFlagNewDir): 
            CMD = "find " + strDir + "/Flag/ -iname \"flag_all_analysis_done\""
            #print(CMD)                
            if subprocess.getoutput(CMD) != "":
                bAllDoneFlagNew = True
        
#         print("bAllDoneFlagOld", bAllDoneFlagOld)
#         print("bAllDoneFlagNew", bAllDoneFlagNew)
        
        if bAllDoneFlagOld or bAllDoneFlagNew:
            self.bPrimaryDone = True
        
        #Set Flowcell Dir 
        self.strRootDir = strDir
        self.strRunID = os.path.basename(strDir)
        
        #Set Log Dir 
        if self.strPlatform =="HiSeq":
            self.strLogDir = HISEQLogDir
        elif self.strPlatform =="MiSeq":
            self.strLogDir = MISEQLogDir
        elif self.strPlatform =="NextSeq":
            self.strLogDir = NEXTSEQLogDir
        else:
            self.strLogDir = OTHERLogDir    
    
    def UpdateRNAStatus(self):        
        #1: Skip unfinished flowcell (unfinished means: primary pipeline does not finished)
        if not self.bPrimaryDone:
            return    
            
        #Check If no RNA pipeline folder  
        strRNADir = self.strRootDir + "/" + RNAPipelineFolder            
        print("Git Repo Exist:", os.path.exists(strRNADir), "-->", strRNADir)
#         if os.path.exists(strRNADir):
#             CMD = "rm -r " + strRNADir
#             os.system(CMD)
            
        if not os.path.exists(strRNADir):
            #This is a new flowcell
            self.bRNANew = True            
        else:
            #Check if pipeline is  done
            strRNADone = self.strRootDir + "/" + RNAPipelineFolder + "/" + DONEFlagRNA
            if os.path.exists(strRNADone):
                self.bRNADone = True
            
            #Check if missing the running flag if there is no Done flag            
            strRNAWorking = self.strRootDir + "/" + RNAPipelineFolder + "/" + WORKINGFlagRNA            
            if not self.bRNADone and not os.path.exists(strRNAWorking):
                self.bAbnomralFlag = True
            elif self.bRNADone and os.path.exists(strRNAWorking): # we do not allow run and done flag exsited as the same time
                self.bAbnomralFlag = True
                self.bRNADone = False                                
                                                    
            #Check if email has been sent
            strRNAEmailSent = self.strRootDir + "/" + RNAPipelineFolder + "/" + DONEFlagEmail
            if os.path.exists(strRNAEmailSent):
                self.bRNAEmailSent = True                        
                            
            #Check if there is anything wrong for current RNA pipeline analysis 
            if not self.bRNADone and not self.bRNAEmailSent and not self.bAbnomralFlag:
                strLogDir = self.strRootDir + "/" + RNAPipelineFolder + "/logs"
                vDir = os.listdir(strLogDir)
                print("Log Dir Len:", len(vDir))             
                if os.path.exists(strLogDir) and len(vDir) != 0:
                    #(1)Check If it contain error msg
                    # 1) Get wrapper log file                
                    CMD = "find " + strLogDir + " -iname \"wrapper.*\""
                    strOutput = subprocess.getoutput(CMD)
                    vWrapperLog = []
                    if strOutput != "":
                        vWrapperLog = strOutput.split("\n")
                    for strLog in vWrapperLog:
                        CMD = "grep -i '" + ERRORMsg + "' " + strLog
                        strOutput = subprocess.getoutput(CMD)
                        if strOutput != "": # contain error
                            self.bErrorMsg = True
                            self.strErrorLog = strLog
                            break                         
                                                   
                    #(2)Check the latest updated log file                
                    CMD = "stat -c %Y " + strLogDir + "/* | sort | tail -n 1"
                    iLastestFileTime = int(subprocess.getoutput(CMD).strip())
                    CMD = "date +%s"
                    iCurTime = int(subprocess.getoutput(CMD).strip())
                    iDiffTime = (iCurTime - iLastestFileTime) / 60 #convert to mins
                    if iDiffTime > (MAXNoUpdateHours * 60): # 12 hours
                        self.bAbnormalJob = True
                        #Get latest log file
                        CMD = "ls -Art " + strLogDir + " | tail -n 1"
                        strOutput = subprocess.getoutput(CMD)     
                        self.strZombieLog = strLogDir + "/" + strOutput
                else:
                    #No std logs dir can be found 
                    self.bMissingDir = True
                    self.strMissingDir = strLogDir           
    
    def UpdateFileList(self, fW, fD):
        # 1: Wait until the primary has been done
        if not self.bPrimaryDone:
            return 1
        
        strRNAGitDir = self.strRootDir + "/" + RNAPipelineFolder
        
        # 2: If primary has been done
        if self.bRNANew: 
            fW.write(self.strRootDir)
            fW.write("\n")            
            return 0            
        elif self.bRNADone:
            fD.write(self.strRootDir)
            fD.write("\n")
            #Check if need to send email
            if not self.bRNAEmailSent:
                #Reset group permission of RNA Pipeline folder in current flowcell
                self.SetGroupPermission(strRNAGitDir)                                
                
                #Send email & add new email done flag
                strMsg = "============ " + self.strRunID + " ============ \\n\\n"
                strMsg += ("Good News    : " + self.strRunID + " IS ALL SET (RNA QC Pipeline) \\n\\n" +
                           "Flowcell Path: " + self.strRootDir) 
                                                                                    
                strSubject = self.strRunID + " is all Set (RNA QC Pipeline)"                
                CMD = "echo -e \"" + strMsg + "\" | mail -r " + EMAILSender + " -s \"" + strSubject + "\" " + EMAILReceiverEnd            
                print(CMD)               
                os.system(CMD)                 
                #2: Set working flag to done and                
                CMD = "touch " + self.strRootDir + "/" + RNAPipelineFolder + "/" + DONEFlagEmail
                os.system(CMD)
                print("Email has been sent successfully! -->", self.strRunID)
            else:
                print("Analysis has been finished! -->", self.strRunID)            
        else:
            strStatus = "RNA QC Pipeline is still Running:"
            strFlagWarningEmail = self.strRootDir + "/" + RNAPipelineFolder + "/" + DONEFlagWarningEmail            
            #Check if need to set warning email -->
            #Sent warning email
            if not os.path.exists(strFlagWarningEmail):
                #1: For abnormal flag (right now the case is: have git repo, however, the flowcell is not done but there is no running flag)
                if self.bAbnomralFlag:
                    #Reset group permission of RNA Pipeline folder in current flowcell
                    self.SetGroupPermission(strRNAGitDir)  
                
                    #--> Reset group permission of RNA Pipeline folder in current flowcell
                    CMD="find " + strRNAGitDir + " -type d -exec chmod g+x {} \;"
                    os.system(CMD)
                    #<-- 
                    
                    #Send it
                    strMsg = "============ " + self.strRunID + " ============\\n\\n"
                    strMsg += ("Warning      : " + self.strRunID + " --> abnormal flags\\n\\n" +
                               "Flowcell Path: " + self.strRootDir + "\\n\\n" +
                               "Errors       : no running flag or both running and done flag. Something wrong?") 
                                                                                        
                    strSubject = self.strRunID + ": Warning (RNA QC Pipeline, Abnormal Flags)"
                    CMD = "echo -e \"" + strMsg + "\" | mail -r " + EMAILSender + " -s \"" + strSubject + "\" " + EMAILReceiverWarning            
                    print(CMD)               
                    os.system(CMD)
                    #create flag to avoid sending multiple times
                    CMD = "touch " + strFlagWarningEmail
                    os.system(CMD)
                    print("Warning email has been sent successfully! -->", self.strRunID)
                    strStatus = "RNA QC Pipeline gets abnormal flags status:"
                #2: No std logs folder
                elif self.bMissingDir:
                    #Reset group permission of RNA Pipeline folder in current flowcell
                    self.SetGroupPermission(strRNAGitDir)
                    
                    #Send it
                    strMsg = "============ " + self.strRunID + " ============\\n\\n"
                    strMsg += ("Warning                   : " + self.strRunID + " --> Missing/Abnormal STD Directory\\n\\n" +
                               "Flowcell Path             : " + self.strRootDir + "\\n\\n" +
                               "Missing/Abnormal Directory: " + self.strMissingDir) 
                                                                                        
                    strSubject = self.strRunID + ": Warning (RNA QC Pipeline, Missing/Abnormal standard directory)"
                    CMD = "echo -e \"" + strMsg + "\" | mail -r " + EMAILSender + " -s \"" + strSubject + "\" " + EMAILReceiverWarning            
                    print(CMD)               
                    os.system(CMD)
                    #create flag to avoid sending multiple times
                    CMD = "touch " + strFlagWarningEmail
                    os.system(CMD)
                    print("Warning email has been sent successfully! -->", self.strRunID)
                    strStatus = "RNA QC Pipeline missing/abnormal STD Dir:"
                #3: For snakemake failed
                elif self.bErrorMsg:
                    #Reset group permission of RNA Pipeline folder in current flowcell
                    self.SetGroupPermission(strRNAGitDir)
                    
                    #Send it
                    strMsg = "============ " + self.strRunID + " ============\\n\\n"
                    strMsg += ("Warning      : " + self.strRunID + " --> ERROR jobs\\n\\n" +
                               "Flowcell Path: " + self.strRootDir + "\\n\\n" +
                               "Error Msg Log: " + self.strErrorLog) 
                                                                                        
                    strSubject = self.strRunID + ": Warning (RNA QC Pipeline, Error Msg in Log)"
                    CMD = "echo -e \"" + strMsg + "\" | mail -r " + EMAILSender + " -s \"" + strSubject + "\" " + EMAILReceiverWarning            
                    print(CMD)               
                    os.system(CMD)
                    #create flag to avoid sending multiple times
                    CMD = "touch " + strFlagWarningEmail
                    os.system(CMD)
                    print("Warning email has been sent successfully! -->", self.strRunID)
                    strStatus = "RNA QC Pipeline contains ERROR:"
                #4: For zombie jobs
                elif self.bAbnormalJob:
                    #Reset group permission of RNA Pipeline folder in current flowcell
                    self.SetGroupPermission(strRNAGitDir)
                    
                    #Send it
                    strMsg = "============ " + self.strRunID + " ============\\n\\n"
                    strMsg += ("Warning        : " + self.strRunID + " --> Long Time No Update\\n\\n" +
                               "Flowcell Path  : " + self.strRootDir + "\\n\\n" +
                               "Zombie Log     : " + self.strZombieLog + "\\n\\n" +
                               "Additional Info: " + "try to unlock the directory and auto-resubmit the submit.sh again. Please manually check the result if you received this warning email multiple times!") 
                                                                                        
                    strSubject = self.strRunID + ": Warning (RNA QC Pipeline, Long Time No Update)"
                    CMD = "echo -e \"" + strMsg + "\" | mail -r " + EMAILSender + " -s \"" + strSubject + "\" " + EMAILReceiverWarning            
                    print(CMD)               
                    os.system(CMD)
                    #create flag to avoid sending multiple times
                    CMD = "touch " + strFlagWarningEmail
                    os.system(CMD)
                    print("Warning email has been sent successfully! -->", self.strRunID)
                    strStatus = "RNA QC Pipeline long time no update (auto-resubmit again):"
                    
                    #--> Based on Mia's requirement(02/05/2021):
                    # Step1: remove the flag "warning email sent"
                    CMD = "rm " + strFlagWarningEmail
                    os.system(CMD)
                    # Step2: unlock RNA QC pipeline Dir
                    strRNAQCPipelineDir = self.strRootDir + "/" + RNAPipelineFolder 
                    CMD = "cd " + strRNAQCPipelineDir + " && snakemake --unlock"
                    os.system(CMD)
                    # Step3: resubmit "submit.sh"
                    CMD = "cd " + strRNAQCPipelineDir  + " && bash " + "submit.sh"                    
                    print(CMD, "\n")
                    os.system(CMD)
                    #<--                  
            #<--
            fW.write(self.strRootDir)
            fW.write("\n")
            print(strStatus, self.strRootDir)        
        print("\n")    
        return 1        
    
    def SetGroupPermission(self, strDir): # solve the issue of "S"
        if not os.path.exists(strDir):
            return
        CMD="find " + strDir + " -type d -exec chmod g+rwx {} \;"
        os.system(CMD)
        CMD="find " + strDir + " -type f -exec chmod g+rw {} \;"
        os.system(CMD)
        
        #update the permission for the files in dropbox
        if not os.path.exists(DROPBOXDir):
            return
        CMD="find " + DROPBOXDir + " -type f -exec chmod g+rw {} \;"
        os.system(CMD)
        
    def Print(self):
        print("bPrimaryDone :", self.bPrimaryDone)
        print("bRNADone     :", self.bRNADone)                        
        print("bRNANew      :", self.bRNANew)
        print("bRNAEmailSent:", self.bRNAEmailSent)
        print("strPlatform  :", self.strPlatform)
        print("strRunID     :", self.strRunID)
        print("strRootDir   :", self.strRootDir)
        print("strLogDir    :", self.strLogDir)
        print("\n", "------------------", "\n")
                
# We also send email in this step
def ProcessData(vFlowcell):
    '''
    1: Update File list
       (1) update new file list 
       (2) send email 
    2: Check new file list    
    3: Run Mia's pipeline
    Go!!
    '''    
    if len(vFlowcell) == 0:
        return
    
    # All flowcell should belong to one type of sequence 
    strWorkingList = vFlowcell[0].strLogDir + "/" + RNAWorkingList
    strDoneList = vFlowcell[0].strLogDir + "/" + RNADoneList
    
    # 1: Update File list        
    fW = open(strWorkingList, "w")
    fD = open(strDoneList, "w")
    vNewFlowcell = []        
    for objFlowcell in vFlowcell:
        iReturn = objFlowcell.UpdateFileList(fW, fD)
        if iReturn == 0:
            vNewFlowcell.append(objFlowcell)            
    fW.close()
    fD.close()
    #delete the x permission 
    CMD = "chmod -x " + strWorkingList
    os.system(CMD)
    CMD = "chmod -x " + strDoneList
    os.system(CMD)
        
    #2: Run Mia's pipeline
    if len(vNewFlowcell) != 0:
        #Send email to let notify people
        #Call Mia's pipeline
        for objFlowcell in vNewFlowcell:
            #1: Check if folder is existed
            strGitDir = objFlowcell.strRootDir + "/" + RNAQCRepoDirName
#             print("Git Repo Exist:", os.path.exists(strGitDir))
#             if os.path.exists(strGitDir):
#                 CMD = "rm -r " + strGitDir
#                 os.system(CMD)
                
            if not os.path.exists(strGitDir):
#                 CMD = "mkdir -p " + strGitDir
#                 os.system(CMD)
#                 CMD = "chmod u+rwx " + strGitDir
#                 os.system(CMD)
#                 CMD = "find " + RNAQCRepoHPC + " -maxdepth 1 -type f -exec cp {} " + strGitDir + " \;"                                
#                 os.system(CMD)
#                 CMD = "find " + strGitDir + " -maxdepth 1 -type f -iname '*.sh' -exec chmod +x {} \;"
#                 os.system(CMD)
#                 CMD = "find " + strGitDir + " -maxdepth 1 -type f -exec dos2unix {} \;"
#                 os.system(CMD)
                #1: We use git here to grab the source code
                CMD = "cd " + objFlowcell.strRootDir + " && git clone " + RNAQCRepoURL
                os.system(CMD)                
                #2: We change the group setting at this point first (solve the issue of "S")
                CMD="find " + strGitDir + " -type d -exec chmod g+rwx {} \;"
                os.system(CMD)
                CMD="find " + strGitDir + " -type f -exec chmod g+rw {} \;"
                os.system(CMD)
                              
            #1: Call mia's pipeline
            os.chdir(strGitDir)
            CMD = "cd " + strGitDir  + " && bash " + "submit.sh"
            #CMD = "cd " + strGitDir + " && ./submit.sh"
            print(CMD, "\n")
            os.system(CMD)
            
            #2: send email notification (start)            
            strMsg = "============ " + objFlowcell.strRunID + " ============\\n\\n"
            strMsg += ("Notification  : " + objFlowcell.strRunID + "has been launched\\n\\n" +
                       "Flowcell Path: " + objFlowcell.strRootDir + "\\n\\n" +
                       "Status       : A new RNA QC pipeline has been launched") 
                                                                                                    
            strSubject = objFlowcell.strRunID + ": RNA QC pipeline has been launched"                
            CMD = "echo -e \"" + strMsg + "\" | mail -r " + EMAILSender + " -s \"" + strSubject + "\" " + EMAILReceiverStart            
            print(CMD)               
            os.system(CMD)
                                                               

def CheckDirExist(strRootDir, strName):
    CMD = "find " + strRootDir + " -maxdepth 1 -iname \"" + strName + "\""
    strTmp = subprocess.getoutput(CMD)
    if strTmp == "":
        return False
    else:
        return True

def main():
    strDataDir = sys.argv[1]
    
    #Print time stamp -->
    print("====== RNA QC Pipeline: Run Mini QC pipeline ======", flush=True)
    print("strDataDir:", strDataDir)
    os.system("date")
    print()
    #<--
    
    #1: Get the status of each flowcell
    vFlowcell = []
    for root, dirs, files in os.walk(strDataDir):                
        for item in dirs:
            strSubDir = os.path.join(root, item)
            #Check if this folder contains the necessary folders
            #Check CASAVA            
            bFindCASAVA = CheckDirExist(strSubDir, "CASAVA")            
            #Check logs
            bFindLogs = CheckDirExist(strSubDir, "logs")            
            #Check reports
            bFindReports = CheckDirExist(strSubDir, "reports")
            #Check csv file 
            bFindCSV = CheckDirExist(strSubDir, "*.csv")                        
            if bFindCASAVA and bFindLogs and bFindReports and bFindCSV:
                objFlowcell = ClsFlowcell()
                objFlowcell.Init(strSubDir)                
                if objFlowcell.iDataType == DICDataType["RNA"]:
                    print(objFlowcell.strRootDir, "-->", objFlowcell.iDataType, " -- ", objFlowcell.strCaptureKit)
                    objFlowcell.UpdateRNAStatus()                
                    objFlowcell.Print()
                    vFlowcell.append(objFlowcell)
        break
    
    #2: Update File list           
    ProcessData(vFlowcell)
    print()     

if __name__ == "__main__":        
    main()
