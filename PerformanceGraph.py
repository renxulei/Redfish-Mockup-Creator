# Copyright Notice:
# Copyright 2019 Lenovo. All rights reserved.
# License: Apache License. For full text see link: https://github.com/renxulei/Redfish-Mockup-Creator/blob/master/APACHE_LICENSE

# -*- coding: utf-8 -*-
import argparse
import collections
import json
import logging
import os
import shutil
import sys
import redfishMockupCreate
from datetime import datetime

curdir = os.path.dirname(__file__)
logdir = os.path.join(curdir, 'PerformanceGraphLogs/')
if not (os.path.exists(logdir)):
    os.mkdir(logdir)

log_file = os.path.join(logdir, "output.log")

def GenerateTimeDict(MockupPath, TimeDict):

    odataid = time = ""

    # recusive go through all directories under mockup folder
    MockupPathDirFile = os.listdir(MockupPath)
    for DirFileElem in MockupPathDirFile:
        DirFilePath = os.path.join(MockupPath, DirFileElem)
        logging.info("Processing directory :" + DirFilePath)
        if(os.path.isdir(DirFilePath)):
            DirFilePathList = DirFilePath.split("\\")
            CurrentParentName = DirFilePathList[-1]
            # skip the first redfish v1/
            if(CurrentParentName == "redfish"):
                GenerateTimeDict(DirFilePath, TimeDict)
                logging.debug("Skip redfish directory without actual result")
            else:
                if(os.path.exists(DirFilePath + "\\index.json") and os.path.exists(DirFilePath + "\\time.json")):
                    try:
                        with open(DirFilePath + "\\index.json", "r") as f:
                            try:
                                fcontent = json.load(f)
                                odataid = fcontent["@odata.id"]
                                if (isinstance(odataid, dict)):
                                    logging.debug("Dict type odataid found")
                                    odataid = fcontent["@odata.id"]["1"]["@odata.id"][:-2]
                            except ValueError:
                                logging.error("Fail to read odataid under " + DirFilePath + ", Generate time dictionary failed")
                                sys.exit(-1)
                            finally:
                                f.close()
                        with open(DirFilePath + "\\time.json", "r") as f:
                            try:
                                fcontent = json.load(f)
                                time = fcontent["GET_Time"]
                            except ValueError:
                                logging.error("Fail to read time under " + DirFilePath + ", Generate time dictionary failed")
                                sys.exit(-1)
                            finally:
                                f.close()
                    except Exception:
                        logging.error("Fail to read file under " + DirFilePath + ", Generate time dictionary failed")
                        sys.exit(-1)
                else:
                    logging.warning("Index.json or time.json doesn't exist under " + DirFilePath + ", Skip this directory")
                        
                TimeDict[odataid] = time
                GenerateTimeDict(DirFilePath, TimeDict)

        else:
            continue

    return TimeDict

def GetReadmeData(MockupPath):

    rhost = averageResponseTime = totalResponseTime = ""

    if(os.path.exists(MockupPath + "\\README")):
        try:
            with open(MockupPath + "\\README", "r") as f:
                try:
                    contents = f.readlines()
                    for line in contents:
                        line_val_list = line.split(":")
                        if("rhost" in line):
                            rhost = line_val_list[1].strip()
                        if("averageResponseTime" in line):
                            averageResponseTime = line_val_list[1].strip() + " sec"
                        if("totalResponseTime" in line):
                            totalResponseTime = line_val_list[1].strip() + " sec"
                except ValueError:
                    logging.error("Fail to read result info from README")
                    return False
        except IOError:
            logging.error("Fail to read README file under mockup directory")
            return False
        finally:
            f.close()
    else:
        logging.error("README file under mockup directory doesn't exist")
    
    return rhost, averageResponseTime, totalResponseTime


def GeneratePerformanceGraph(TimeDict, HostIP, AverageTime, TotalTime, ExceptAverage):

    chart_data = {

        "legend": ["Time"],
        "xAxis": [],
        "rows": [],
        "series": {
            "Time": [],
        },
        'colors': {
            'Time': '#99EEEE',
            'realtime': '#9999EE',
            # 'variance': 'black'
        },
        'types': {
            'Time': 'bar',
            'realtime': 'bar'
            # 'variance': 'line'
        },
    }
    xAxis = chart_data["xAxis"]
    rows = chart_data["rows"]
    se_Time = chart_data["series"]["Time"]
    for url, arr in sorted(TimeDict.items(), key=lambda x: x[0]):
        if (url == "" or arr == ""):
            continue
        xAxis.append(url)
        Time_val = int(float(arr)*1000)
        se_Time.append(Time_val)
        rows.append({"time": Time_val, "url": url, "rounds": Time_val})

    try:
        template_path = os.path.join(curdir, "template.html")
        templateHtml = open(template_path, encoding= 'utf-8').read()
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        outfp = os.path.join(logdir, "result" + timestamp + ".html")
    except IOError:
        logging.error("Fail to open template page")
        return False

    templateHtml = templateHtml.replace("{{title}}", "Redfish Performance Test Result %s" % timestamp
        ).replace('{{HostIP}}', HostIP).replace('{{AverageTime}}', AverageTime).replace('{{TotalTime}}', TotalTime)

    if (ExceptAverage[0] < (float(AverageTime[:-4]))):
        print("Average time beyond expect, mockup data result FAIL the test")
    else:
        print("Average time within expect, mockup data result PASS the test")
    print("Expect average time: %f" %(ExceptAverage[0]))
    print("Actual average time: %f" %(float(AverageTime[:-4])))

    try:
        with open(outfp, 'w') as outf:
            outf.write(templateHtml.replace("{{jsondata}}", json.dumps(chart_data, sort_keys=True, indent=True)))
            outf.flush()
    except IOError:
        logging.error("Fail to write Json data into template page")
        return False

    return outfp

    
def main():
    
    TimeDict= {}

    mkparser = argparse.ArgumentParser(description='Tool for generate performancegraph from mockup data.')

    mkparser.add_argument('--dir', type=str, required=True, help='directory of mockup creator data', dest="Dir")
    mkparser.add_argument('--expect', type=float, required=True, nargs=1, help='expect average response time', dest="ExceptAverage")

    mkparser.add_argument("use_mockup", nargs='?', choices=["mockupargs"], help="command name")
    mkparser.add_argument("mockup_args", nargs=argparse.REMAINDER, help=argparse.SUPPRESS) 

    args = mkparser.parse_args()

    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s',
                datefmt='%a, %d %b %Y %H:%M:%S',
                filename=log_file,
                filemode='w',
                )
                
    console = logging.StreamHandler(stream=sys.stdout)
    console.setLevel(logging.ERROR)
    formatter = logging.Formatter('%(levelname)-8s: %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

    if not ("-T" in args.mockup_args):
        args.mockup_args.append("-T")

    if not ("-S" in args.mockup_args):
        args.mockup_args.append("-S")

    if(args.use_mockup is not None):
        try:
            mockup_args_list = [args.use_mockup] + args.mockup_args + ["-D", args.Dir]
            redfishMockupCreate.main(mockup_args_list)
        except SystemExit as e:
            if(e.code == 0):
                pass
            else:
                sys.exit(e)

    logging.info("Tool start at " + datetime.now().strftime('%Y%m%d%H%M%S') + " with Mockup data from " + args.Dir)

    if (os.path.exists(args.Dir)):
        MockupPath =  args.Dir
    else:
        logging.error("Mockup file directory doesn't exist")
        return False
    
    print("Generating time dictionary from mockup data ...")
    TimeDict = GenerateTimeDict(MockupPath, TimeDict)

    print("Reading data from README file ...")
    HostIP, AverageTime, TotalTime, = GetReadmeData(MockupPath)
    if (HostIP == "" or AverageTime == "" or TotalTime ==""):
        logging.error("Get data from README file failed")
        return False
 
    print("Generating PerformanceGraph ...")
    ret = GeneratePerformanceGraph(TimeDict, HostIP, AverageTime, TotalTime, args.ExceptAverage)
    if (ret != False):
        print("Please check result page under " + ret + " and output.log under " + logdir)
    else:
        logging.error("Generating PerformanceGraph failed")
        return False

    logging.info("Tool exit at " + datetime.now().strftime('%Y%m%d%H%M%S'))

    
if __name__ == "__main__":
    
    main()
