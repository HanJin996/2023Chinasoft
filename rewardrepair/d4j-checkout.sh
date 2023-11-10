#! /bin/bash
# 可以从member.txt的名单中，checkout所需的D4J project
USE_TIMESTAMP=0
LOG_RESULT=0

while [ "$1" != "" ]; do
  case $1 in
    -l | --log-result )
      LOG_RESULT=1      
      ;;
    -t | --timestamp )
      USE_TIMESTAMP=1
      ;;
  esac
  shift
done

echo "start"

CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
DEFECTS4J_DIR=/home/lqy/Workspace/rewardrepair/MyCode/MyData/Defects4J_projects
CONTINUOUS_LEARNING_DATA=$CURRENT_DIR/../Continuous_Learning/public/single_run_data

echo "Creating directory 'Defects4J_projects'"
mkdir -p $DEFECTS4J_DIR
echo

echo "Reading from rewardrepair-member.txt"
while IFS=_ read -r col1 col2
do
  col2=$(echo "$col2" | tr -d '\r' | tr -d '\n')  # 去掉回车符和换行符
  echo $col1 $col2
  BUG_PROJECT=${DEFECTS4J_DIR}/${col1}_${col2}
  mkdir -p $BUG_PROJECT
  # echo $col1 ${col2}b $BUG_PROJECT
  /home/lqy/defects4j/framework/bin/defects4j checkout -p $col1 -v ${col2}b -w $BUG_PROJECT 
  # &>/dev/null
  echo
done < /home/lqy/Workspace/rewardrepair/MyCode/MyData/member.txt

echo "done"
echo
exit 0