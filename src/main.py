from mss import mss
from PIL import Image
import pytesseract
from pytesseract import Output
# for more type tricks etc: https://peps.python.org/pep-0484
from typing import cast
import os


def main() -> None:
    fullScreenShot()


def fullScreenShot(imageName: str = "tmp") -> None:
    with mss() as sct:
        imagePath: str = f"images/{imageName}.png"
        dirName: str = os.path.dirname(imagePath)
        if not os.path.exists(dirName):
            os.makedirs(dirName)

        screenShot: str = sct.shot(output=imagePath)
        print(screenShot)

        image : Image.Image = Image.open(imagePath)
        result: dict[str, str] = cast(
            dict[str, str], pytesseract.image_to_data(image, output_type=Output.DICT))
        print(result)


if __name__ == "__main__":
    main()
