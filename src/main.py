from mss import mss
from PIL import Image
import pytesseract
from pytesseract import Output
# for more type tricks etc: https://peps.python.org/pep-0484
from typing import List, Tuple, cast, TypedDict
import os
import pyautogui
import time
from pynput import keyboard
from pynput.keyboard import KeyCode, Key
from pynput._util import AbstractListener


# wait time between processing two inputs
intermediate_seconds: float = 0.5  # seconds

# the total input time it takes to input the whole number
per_round_time: float = 0.5  # seconds


def main_loop() -> None:
    num: int = getNumber()
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


def main() -> None:

    global intermediate_seconds

    # ...or, in a non-blocking fashion:
    listener: keyboard.Listener = keyboard.Listener(
        on_press=on_press,
        on_release=on_release
    )
    listener.start()

    while True:
        if run_status == "1":
            main_loop()
            time.sleep(intermediate_seconds)
        elif run_status == "2":
            break
        else:
            time.sleep(1/4)


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
        "L": "1"
    }

    result = inp
    for key in replacement_dict.keys():
        result = result.replace(key, replacement_dict[key])

    return result


def parseNumber(_text: List[str]) -> int:
    text: list[str] = list(filter(lambda item: item != "", _text))
    if len(text) < 3:
        raise Exception(f"the ocr text is to short: {len(text)}")
    num = text[2]
    if num.isnumeric():
        return int(num)

    new_num: str = fixOCRIssues(num)

    if new_num.isnumeric():
        return int(new_num)

    print(text)
    raise Exception(f"couldn't parse the number from OCR: '{new_num}'")


def getNumber(imageName: str = "tmp") -> int:
    with mss() as sct:
        imagePath: str = f"images/{imageName}.png"
        dirName: str = os.path.dirname(imagePath)
        if not os.path.exists(dirName):
            os.makedirs(dirName)

        sct.shot(mon=1, output=imagePath)

    # took screenshot, reduce nesting here
    image: Image.Image = Image.open(imagePath)

    box: Tuple[int, int, int, int] = (800, 500, 1100, 550)
    cropped: Image.Image = image.crop(box)
    # cropped.save("images/cropped.png")

    result: ParsedText = cast(
        ParsedText, pytesseract.image_to_data(cropped, output_type=Output.DICT))

    text: List[str] = result["text"]
    if (len(text) == 0):
        raise Exception("the result from the tesseract ocr is an empty list")

    return parseNumber(text)


if __name__ == "__main__":
    main()
