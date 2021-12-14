import sys
import pandas
import os
import subprocess

ROOTDropBoxDir = "/CGF/Laboratory/LIMS/drop-box-prod/RNAsequenceqc"
ROOTProjDir = "/CGF/Laboratory/Projects"
    
class ClsSample:
    def __init__(self):
        self.strName = ""
        self.strBarcode = ""
        self.strProjID = ""

def GetProjectList(strSamplesheet, vProjIDList, vSample):
    with open(strSamplesheet, 'r') as ssfile:
        # identify which lines to skip before reading in the Data table
        # the [Data] line may have commas or may not, so this identifies the proper line
        sslines = ssfile.readlines()
        dataline = [x for x in sslines if x.startswith('[Data]')][0]
        skiphere = sslines.index(dataline)

    dfss = pandas.read_table(strSamplesheet, sep=',', skiprows=skiphere+1)
    
    # Get Sample Name and project ID pair
    vSampleName = dfss["Sample_Name"].tolist()
    #print(vSampleName)
    vProjID = [tmpID.replace('Project_', '') for tmpID in dfss["Sample_Project"].tolist()]
    for i in range(0, len(vSampleName)):
        objSample = ClsSample()
        objSample.strName = vSampleName[i].split('-')[0]
        objSample.strBarcode = "-".join(vSampleName[i].split('-')[1:])
        objSample.strProjID = vProjID[i]
        # print(objSample.strName)
        # print(objSample.strBarcode)
        # print(objSample.strProjID)
        vSample.append(objSample)    
    
    # Kristie's final table needs 4 columns at the beginning:
    # Sample, Barcode (Index-Index2), Lane, Project
    tmpList = [tmpID.replace('Project_', '') for tmpID in dfss['Sample_Project'].unique().tolist()]
    #print("vProjIDList", tmpList)
    for projID in tmpList:
        vProjIDList.append(projID)

def UpdateReport(strQCReport, vSample):
    #Build dict for vSample
    dictSample = {}
    for objSample in vSample:                
        dictSample[objSample.strName + "-" + objSample.strBarcode] = objSample.strProjID
    #print(dictSample)
    
    #Get the first row from org file
    strInfo = subprocess.getoutput("head -n 1 " + strQCReport) + "\n"
    #print(strInfo)
    
    dfqcr = pandas.read_table(strQCReport, sep='\t', skiprows=1)
    for i in range(0, len(dfqcr)):
        strKey = dfqcr.loc[i]["Sample"] + "-" + dfqcr.loc[i]["Barcode"]  
        #print(strKey)
        dfqcr.at[i, "Project"] = dictSample[strKey]
    #print(dfqcr["Project"])
    with open(strQCReport, 'w') as fp:
        fp.write(strInfo)
        dfqcr.to_csv(fp, index=False, sep='\t')
    #dfqcr.to_csv('out.csv', index=False, sep='\t')

    
def BackupProjectReport(strQCReport, mrID, runID, strProjID, vSample):
    # Get the target folder
    strProjectDir = ROOTProjDir + "/" + mrID + "/" + strProjID + "/Reports"
    strProjectReport = strProjectDir + "/" + runID + "_qc_lims_table.txt"
    
    if not os.path.exists(strProjectDir):
        CMD = "mkdir -p " + strProjectDir 
        os.system(CMD)
        
    # Write content into strProjectReport
    print("strProjectReport:", strProjectReport)
    CMD = "head -n 2 " + strQCReport + " > " + strProjectReport
    os.system(CMD)
    for objSample in vSample:
        if objSample.strProjID == strProjID:
            CMD = "grep -i " + "'" + strProjID + "' " + strQCReport + " | grep -i '" + objSample.strName + "' >> " + strProjectReport
            os.system(CMD)

# def main():
#     strSamplesheet = sys.argv[1]
#     strQCReport = sys.argv[2]
#     mrID = sys.argv[3]
#     runID = sys.argv[4]
def BackupReport(strSamplesheet, strQCReport, mrID, runID):    
    #get project list
    vProjIDList = []
    vSample = []
    GetProjectList(strSamplesheet, vProjIDList, vSample)
    #print("vProjIDList", vProjIDList)
    if len(vProjIDList) == 0:
        print("Error: fail to find project ID in samplesheet!")
        return 1
    
    if len(vProjIDList) != 1:
        UpdateReport(strQCReport, vSample)
        
    #back up QC report to Drop box
    #1: Copy it to dropbox
    strDropBoxReport = ROOTDropBoxDir + "/" + runID + "_qc_lims_table.txt"
    if not os.path.exists(ROOTDropBoxDir):
        CMD = "mkdir -p " + ROOTDropBoxDir
        #print(CMD)
        os.system(CMD)
    CMD = "cp " + strQCReport + " " + strDropBoxReport
    os.system(CMD)
    print("Done: Copy it to dropbox!")

    #2: Backup it to project report folder
    if len(vProjIDList) == 1:
        #copy it directly
        strProjectDir = ROOTProjDir + "/" + mrID + "/" + vProjIDList[0] + "/Reports"
        strProjectReport = strProjectDir + "/" + runID + "_qc_lims_table.txt"
        if not os.path.exists(strProjectDir):
            CMD = "mkdir -p " + strProjectDir 
            os.system(CMD)
        CMD = "cp " + strQCReport + " " + strProjectReport
        os.system(CMD)
    else:
        # this is the case for multiple different project contained in one flowcell
        print("vProjIDList:", vProjIDList)
        for strProjID in vProjIDList:
            BackupProjectReport(strQCReport, mrID, runID, strProjID, vSample)
    print("All Done: copy has been finished!")
    return 0

if __name__ == "__main__":
    BackupReport(strSamplesheet, strQCReport, mrID, runID)
    #main()
    
