import sys
import liger_iris_pipeline

from liger_iris_pipeline.base_step import LigerIRISStep

def lirun():

    if '--version' in sys.argv:
        sys.stdout.write("%s\n" % liger_iris_pipeline.__version__)
        sys.exit(0)
    try:
        step = LigerIRISStep.from_cmdline(sys.argv[1:])
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
