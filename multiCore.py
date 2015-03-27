# The script is inspired by Menno Straatsma.
# 12 March 2014: Edwin started modifying some lines.

import string
import os 
import sys
import glob
import numpy as np

def filesPerCore(fileList, ncores):
	'''list the number of files mper core resulting in an similar total 
	   file size'''
	coreFileSize = range(-ncores, 0, 1)
	outFileList = []
	for i in range(ncores):
		outFileList.append([])
	for areaFile in fileList:
		areaSize = os.path.getsize(areaFile)
		minCoreIndex = coreFileSize.index(min(coreFileSize))
		coreFileSize[minCoreIndex] += areaSize
		outFileList[minCoreIndex].append(areaFile)
	print('fileSizes: ')
	print(coreFileSize)
	return outFileList

########################################################################

# clone map files that will be used
fileList = glob.glob('/scratch-shared/dfguu/data/hydroworld/others/05ArcMinCloneMaps/new_masks_from_top/clone_M*.map')

# typical ini files
dummy_ini_filename = '/home/edwinhs/github/edwinkost/PCR-GLOBWB/config/setup_dummy.ini'
try:
	dummy_ini_filename = str(sys.argv[1])
except:
	pass	
dummy =  open(dummy_ini_filename,'r').read()

# output directories for model results
outputDirRoot  = '/projects/wtrcycle/users/edwinhs/multi_cores_1960_to_2010/%s/'
try:
	outputDirRoot = str(sys.argv[2])+'/%s/'
except:
	pass	

#-output directory for ini files and batch files 
batchFilePath  = '/home/edwinhs/jobs/multi_core_jobs/batch_files/'
iniFilesPath   = '/home/edwinhs/jobs/multi_core_jobs/ini_files/'
try:
	batchFilePath = str(sys.argv[3])+'/batch_files/'
	iniFilesPath  = str(sys.argv[3])+'/ini_files/'
except:
	pass	

# master job file (that will be submitted as a cartesius job)
masterBatchFile = 'jobs.sh'
try:
	masterBatchFile = str(sys.argv[4])
except:
	pass	

# main python file/script to run the model
modelScriptFolderInAbsolutePath = "/home/edwinhs/github/edwinkost/PCR-GLOBWB/model/"
modelFileName  = modelScriptFolderInAbsolutePath+'deterministic_runner.py'

# to be writen in the ini files: file names for clone, landMask and ldd:
cloneMapPath   = '/scratch-shared/dfguu/data/hydroworld/others/05ArcMinCloneMaps/new_masks_from_top/clone_%s.map'
landmaskPath   = '/scratch-shared/dfguu/data/hydroworld/others/05ArcMinCloneMaps/new_masks_from_top/mask_%s.map'  

# number of cores that will be used
ncores = 53 # from 53 maks

# walltime, number and type of node:
wall_time      = '119:50:00' # '50:00'            # '119:50:00'
number_of_node =  1          # 1                  # 1           #
type_of_node   = 'normal'    # 'short'            # 'fat'       # options are fat, normal and short

# preparing directories:
try:
	os.makedirs(iniFilesPath)
except:
	pass
try:
	os.makedirs(batchFilePath)
except:
	pass
os.system('rm -r '+iniFilesPath+"/*")
os.system('rm -r '+batchFilePath+"/*")

iniFileBase    = 'setup_%s.ini'				   # % (area)  
batchFileBase  = 'batch_%scores_core%s.txt'    # % (ncores, core_i)

########################################################################

############ main ######################################################

cores= range(1,ncores+1)

#- create master batch file and individual batch files for each core
outMaster = open(os.path.join(batchFilePath,masterBatchFile), 'w')
# - write header for the job file
masterLine = '#!/bin/bash\n'
outMaster.write(masterLine)  
masterLine = '#SBATCH -N %i\n' % (number_of_node)
outMaster.write(masterLine)  
masterLine = '#SBATCH -t %s\n' % (wall_time)
outMaster.write(masterLine)  
masterLine = '#SBATCH -p %s\n' % (type_of_node)
outMaster.write(masterLine)
if type_of_node  == 'normal':  
	masterLine = '#SBATCH --constraint=haswell\n'
	outMaster.write(masterLine)  
for coreIdx in cores:
	#-fill master batch file with bash command that starts a single core
	masterLine = 'bash %s & \n' % os.path.join(batchFileBase % (ncores, coreIdx))
	outMaster.write(masterLine)
	#-create a single batch file for each core
	batchFileName = os.path.join(batchFilePath, batchFileBase % (ncores, coreIdx))
	outFileCore = open(batchFileName, 'w')
	outFileCore.close()
outMaster.write('wait \n')
outMaster.close()

#- create a list of files to be processed by each core and write files
filesPerNcores = filesPerCore(fileList, ncores)

for coreIdx in cores:
	for cloneFile in filesPerNcores[cores.index(coreIdx)]:
		
		area = cloneFile[-7:-4]
		
		#- replace strings in dummy file
		d2 = string.replace(dummy, 'OUTPUTDIRECTORY', outputDirRoot%area)
		d3 = string.replace(d2,    'CLONEMAPFILES',    cloneMapPath%area)
		d4 = string.replace(d3,    'LANDMASKFILES',    landmaskPath%area)
		
		last = d4
		
		#- write ini file to disc
		iniOutputName = os.path.join(iniFilesPath, iniFileBase % area)
		outFile = file(iniOutputName, 'w')
		outFile.write(last)
		outFile.close()

		#- list .ini file for "area" in the batch file with least lines
		batchFileNameCore = os.path.join(batchFilePath, batchFileBase%(ncores, coreIdx))
		batchOutFile = file(batchFileNameCore, 'a')
		
		# write python command line
		#~ batchLine = 'numactl --localalloc --physcpubind=%s python /home/beek0120/PCR-GLOBWB/scripts/twoLayersNewSoilParams/PCR-GLOBWB_TwoLayers.py %s\n' % (coreIdx, iniOutputName)
		#~ batchLine = 'numactl --localalloc --physcpubind=%s python %s %s\n' % (coreIdx, modelFileName, iniOutputName)
		
		batchLine = 'python %s %s\n' % (modelFileName, iniOutputName)
		batchOutFile.write(batchLine)

		batchOutFile.close()
		print 'creating %s  and line added to %s' %(iniOutputName, batchFileNameCore)


