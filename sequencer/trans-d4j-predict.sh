#! /bin/bash

echo "sequencer-predict.sh start"

CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
ROOT_DIR="$(dirname "$CURRENT_DIR")"

HELP_MESSAGE=$'Usage: ./sequencer-predict.sh --buggy_file=[abs path] --buggy_line=[int] --beam_size=[int] --output=[abs path]
buggy_file: Absolute path to the buggy file
buggy_line: Line number of buggy line
beam_size: Beam size used in seq2seq model
tmp_dir: Absolute path for output'
for i in "$@"
do
case $i in
    --buggy_file=*)
    BUGGY_FILE_PATH="${i#*=}"
    shift # past argument=value
    ;;
    --buggy_line=*)
    BUGGY_LINE="${i#*=}"
    shift # past argument=value
    ;;
    --beam_size=*)
    BEAM_SIZE="${i#*=}"
    shift # past argument=value
    ;;

    --tmp_dir=*)
    TMP_DIR="${i#*=}"
    shift # past argument=value
    ;;
    --diff_path=*)
    DIFF_PATH="${i#*=}"
    shift # past argument=value
    ;;
    *)
          # unknown option
    ;;
esac
done

if [ -z "$BUGGY_FILE_PATH" ]; then
  echo "BUGGY_FILE_PATH unset!"
  echo "$HELP_MESSAGE"
  exit 1
elif [[ "$BUGGY_FILE_PATH" != /* ]]; then
  echo "BUGGY_FILE_PATH must be absolute path"
  echo "$HELP_MESSAGE"
  exit 1
fi

if [ -z "$BUGGY_LINE" ]; then
  echo "BUGGY_LINE unset!"
  echo "$HELP_MESSAGE"
  exit 1
fi

if [ -z "$BEAM_SIZE" ]; then
  echo "BEAM_SIZE unset!"
  echo "$HELP_MESSAGE"
  exit 1
fi

if [ -z "$TMP_DIR" ]; then
  echo "TMP_DIR unset!"
  echo "$HELP_MESSAGE"
  exit 1
fi 

if [ -z "$DIFF_PATH" ]; then
  echo "DIFF_PATH unset!"
  echo "$HELP_MESSAGE"
  exit 1
fi

echo "Input parameter:"
echo "BUGGY_FILE_PATH = ${BUGGY_FILE_PATH}"
echo "BUGGY_LINE = ${BUGGY_LINE}"
echo "BEAM_SIZE = ${BEAM_SIZE}"
echo "TMP_DIR = ${TMP_DIR}"
echo "DIFF_PATH = ${DIFF_PATH}"
echo

BUGGY_FILE_NAME=${BUGGY_FILE_PATH##*/}
if [[ $BUGGY_FILE_NAME =~ ([^-]+)---([^-]+)---([^-]+)---([^-]+)\.java$ ]]; then
  NEW_BUGGY_FILE_NAME=${BASH_REMATCH[3]}.java
fi
BUGGY_FILE_BASENAME=${BUGGY_FILE_NAME%.*}

# 使用ONMT translate的过程

# echo "Creating temporary directory ${TMP_DIR}"
# mkdir -p $TMP_DIR
# echo

echo "Abstracting the source file"
java -jar /SequenceR/src/lib/abstraction-1.0-SNAPSHOT-jar-with-dependencies.jar $BUGGY_FILE_PATH $BUGGY_LINE $TMP_DIR
retval=$?
if [ $retval -ne 0 ]; then
  echo "Cannot generate abstraction for the buggy file"
  exit 1
fi
echo

echo "Tokenizing the abstraction"
python3 $CURRENT_DIR/Buggy_Context_Abstraction/tokenize.py $TMP_DIR/${BUGGY_FILE_BASENAME}_abstract.java $TMP_DIR/${BUGGY_FILE_BASENAME}_abstract_tokenized.txt
retval=$?
if [ $retval -ne 0 ]; then
  echo "Tokenization failed"
  exit 1
fi
echo

echo "Truncate the abstraction to 1000 tokens"
perl $CURRENT_DIR/Buggy_Context_Abstraction/trimCon.pl $TMP_DIR/${BUGGY_FILE_BASENAME}_abstract_tokenized.txt $TMP_DIR/${BUGGY_FILE_BASENAME}_abstract_tokenized_truncated.txt 1000
retval=$?
if [ $retval -ne 0 ]; then
  echo "Truncation failed"
  exit 1
fi
echo

echo "Generating predictions"
python3 $CURRENT_DIR/lib/OpenNMT-py/translate.py -model /SequenceR/results/Golden/final-model_step_20000.pt -src $TMP_DIR/${BUGGY_FILE_BASENAME}_abstract_tokenized_truncated.txt -output $TMP_DIR/predictions.txt -beam_size $BEAM_SIZE -n_best $BEAM_SIZE 
#&>/dev/null
echo

echo "Post process predictions"
python3 $CURRENT_DIR/Patch_Preparation/postPrcoessPredictions.py $TMP_DIR/predictions.txt $TMP_DIR
retval=$?
if [ $retval -ne 0 ]; then
  echo "Post process generates none valid predictions"
  exit 1
fi
echo

# use it after using trans-d4j-generatePatches.py to generate patches.
# OUTPUT="${TMP_DIR/\/tmp\//\/results\/}"
# echo "Generating diffs"
# for patch in $OUTPUT/*; do
#   diff -u -w $DIFF_PATH $patch/$NEW_BUGGY_FILE_NAME > $patch/diff
# done
# echo

echo "Found $(ls $OUTPUT | wc -l | awk '{print $1}') patches for $NEW_BUGGY_FILE_NAME stored in $OUTPUT"
echo "sequencer-predict.sh done"
echo
exit 0