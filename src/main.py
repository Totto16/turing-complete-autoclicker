from mss import mss
from PIL import Image
import pytesseract
from pytesseract import Output
# for more type tricks etc: https://peps.python.org/pep-0484
from typing import List, Tuple, cast, TypedDict
import os
import json
import shutil
import pyautogui
import time
from pynput import keyboard
from pynput.keyboard import KeyCode, Key
from pynput._util import AbstractListener


# change in here and in the bash script, to get the traineddata
LANG: str = "deu"

# wait time between processing two inputs
intermediate_seconds: float = 0.5  # seconds

# the total input time it takes to input the whole number
per_round_time: float = 0.5  # seconds


def step(act_num: int) -> None:
    num: int = getNumber(f"image_{act_num}")
    bin_num: str = bin(num)[2:]
    bin_num = bin_num.rjust(8, '0')
    print(f"now got number {num}")

    global per_round_time

    click_y: int = 955
    click_x1, click_x2 = (597, 1260)
    amount: int = 8
    click_x_width: float = (click_x2-click_x1)/(amount-1)
    current_point: tuple[int, int] = (click_x1, click_y)
    for char in bin_num:
        pyautogui.moveTo(current_point)

        if char == "1":
            pyautogui.click()

        new_x: int = round(current_point[0]+click_x_width)
        current_point = (new_x, click_y)
        time.sleep(per_round_time/amount)

    # finally click the ok button:
    pyautogui.click((962, 1022))


run_status: str = "0"


def on_press(key: Key | KeyCode | None) -> None:
    # try:
    #     print('alphanumeric key {0} pressed'.format(
    #         key.char))
    # except AttributeError:
    #     print('special key {0} pressed'.format(
    #         key))

    if isinstance(key, Key):
        if key.name == "f3":
            global run_status
            match run_status:
                case "0":
                    run_status = "1"
                    print("now starting")
                case "1":
                    run_status = "2"
                    print("now exiting")
                case _:
                    raise Exception(
                        f"not intended 'run_status' value: {run_status}")

    return None


def on_release(key: Key | KeyCode | None) -> None:
    # print('{0} released'.format(
    #     key))
    # if key == keyboard.Key.esc:
    #     global run_status
    #     # Stop listener
    #     run_status = "2"
    #     return False

    global run_status
    if run_status == "2":
        raise AbstractListener.StopException("")

    return None


imagesDir: str = "images"


def deleteFolder(dir: str) -> None:
    for filename in os.listdir(dir):
        file_path: str = os.path.join(dir, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))


def main() -> None:

    global intermediate_seconds
    global imagesDir

    # if not deleted previously
    deleteFolder(imagesDir)

    listener: keyboard.Listener = keyboard.Listener(
        on_press=on_press,
        on_release=on_release
    )
    listener.start()

    # TODO: detect level and click start button, or if it's not the binary race, then do another detection and input method (like negative numbers e.g.)

    i: int = 0
    try:
        while True:
            if run_status == "1":
                step(i)
                time.sleep(intermediate_seconds)
                i = i+1
            elif run_status == "2":
                break
            else:
                time.sleep(1/4)
    except RuntimeError as e:
        print(e)
        print("did not delete trace images and files")
    except Exception as e:
        print(e)
        deleteFolder(imagesDir)


# typed tesseract output
class ParsedText(TypedDict):
    level: List[int]
    page_num: List[int]
    block_num: List[int]
    par_num: List[int]
    line_num: List[int]
    word_num: List[int]
    left: List[int]
    top: List[int]
    width: List[int]
    height: List[int]
    conf: List[int]
    text: List[str]


def fixOCRIssues(inp: str) -> str:

    replacement_dict: dict[str, str] = {
        "[": "1",
        "]": "1",
        "|": "1",
        "L": "1",
        "/": "7",
        ".": "",
        "in": "",
        "Ü": "0",
        #  "O": "0", # can also be 6 is some cases :(
    }

    result = inp
    for key in replacement_dict.keys():
        result = result.replace(key, replacement_dict[key])

    return result


def parseNumber(_text: List[str], dump_name: str, raw_ocr: ParsedText) -> int:
    text: list[str] = list(filter(lambda item: item != "", _text))
    if len(text) < 3:
        raise Exception(f"the ocr text is to short: {len(text)}")
    num = text[2]
    if num.isnumeric():
        with open(dump_name, 'w') as f:
            json.dump(
                {"success": True, "raw_num": num, "parsed_num": int(num), "input": text}, f)
        return int(num)

    new_num: str = fixOCRIssues(num)

    if new_num.isnumeric():
        with open(dump_name, 'w') as f:
            json.dump({"success": True, "raw_num": new_num, "parsed_num": int(
                new_num), "input": text}, f)
        return int(new_num)

    with open(dump_name, 'w') as f:
        json.dump({"success": False, "raw_num": new_num,
                  "parsed_num": None, "input": text, "raw": raw_ocr}, f)

    raise Exception(
        f"couldn't parse the number from OCR: '{new_num}', text: {text}")


def getNumber(imageName: str = "tmp") -> int:
    with mss() as sct:
        global imagesDir
        imagePath: str = f"{imagesDir}/{imageName}.png"
        dirName: str = os.path.dirname(imagePath)
        if not os.path.exists(dirName):
            os.makedirs(dirName)

        sct.shot(mon=1, output=imagePath)

    # took screenshot, reduce nesting here
    image: Image.Image = Image.open(imagePath)

    box: Tuple[int, int, int, int] = (800, 500, 1100, 550)
    cropped: Image.Image = image.crop(box)
    # cropped.save("images/cropped.png")

    global LANG
    tessdata_dir_config = r'--tessdata-dir "."'

    # TODO: add more variable settings, so that tesseract may give good results in some case:
    # see https://github.com/tesseract-ocr/tesseract/blob/main/doc/tesseract.1.asc

    max_attempts: int = 5
    attempt_config: list[str] = ["", " --psm 6",
                                 " --psm 4", " --psm 7", " --psm 13"]
    if len(attempt_config) < max_attempts:
        raise AssertionError(
            f"The attempts config is to small, it has to be at least {max_attempts} long, but is {len(attempt_config)} long!")

    for attempts in range(max_attempts):
        try:

            result: ParsedText = cast(
                ParsedText, pytesseract.image_to_data(cropped, output_type=Output.DICT, lang=LANG, config=tessdata_dir_config + attempt_config[attempts]))

            text: List[str] = result["text"]
            if (len(text) == 0):
                raise Exception(
                    "the result from the tesseract ocr is an empty list")

            return parseNumber(text, f"{imagesDir}/{imageName}_a{attempts}.json", result)
        except Exception as e:
            print(f"{e} in attempt {attempts}")
            # just ignore and continue
            continue

    raise RuntimeError(
        f"Couldn't parse the number with OCR in {max_attempts} attempts")


if __name__ == "__main__":
    main()
