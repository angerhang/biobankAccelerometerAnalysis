from accelerometer import accUtils
accUtils.writeStudyAccProcessCmds("/well/doherty/users/cxx579/project_data/raine/gen2_22/gt3x/wrist/",
                                  cmdsFile="process-raine-gen2-cmds.txt",
                                  outDir="/well/doherty/users/cxx579/project_data/raine/gen2_22/gt3x/wrist/baseline_oct2",
                                  accExt="gt3x",
                                  cmdOptions="--deleteIntermediateFiles False "+
                                             "--timeZone Australia/Perth "+
                                             "--useFilter False "+
                                             "--npyOutput True "+
                                             "--rawOutput True "+
                                             "--sampleRate 30 "+
                                             "--csvSampleRate 30 "+
                                             "--epochPeriod 30 ")
# <list of processing commands written to "process-cmds.txt">
