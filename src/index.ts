import { randomUUID } from "crypto"
import fs from "fs"
import screenshot from "screenshot-desktop"

export interface ScreenshotObject {
    path: string
    delete: () => void
}

export async function sleep(ms: number) {
    return new Promise((resolve) => setTimeout(resolve, ms))
}

async function takeScreenshot(): Promise<ScreenshotObject> {
    if (!fs.existsSync("tmp/")) {
        fs.mkdirSync("tmp", { recursive: true })
    }

    function getNotUsedName() {
        while (true) {
            const filename = `tmp/${randomUUID()}.png`
            if (!fs.existsSync(filename)) {
                return filename
            }
        }
    }

    const filename = getNotUsedName()

    const imgPath = await screenshot({ filename, screen: 0 })

    return {
        path: imgPath,
        delete: () => {
            fs.unlinkSync(imgPath)
        },
    }
}

async function startLoop() {
    const firstScreenshot = await takeScreenshot()
    console.log(firstScreenshot)
    await sleep(30000)
    firstScreenshot.delete()
}

export interface GlobalState {
    start: boolean
    stop: boolean
}

const state: GlobalState = {
    stop: false,
    start: false,
}

async function start() {
    process.on("exit", () => {
        fs.rmdirSync("tmp", { recursive: true })
    })

    await startLoop()
}

start()
