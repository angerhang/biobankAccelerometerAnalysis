from accelerometer import accUtils
accUtils.writeStudyAccProcessCmds("/well/doherty/projects/raine/gen1_26/gt3x/wrist/",
                                  cmdsFile="process-raine-gen1-cmds.txt",
                                  outDir="/well/doherty/projects/raine/gen1_26/gt3x/wrist/baseline_oct8",
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
