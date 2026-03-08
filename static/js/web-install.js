// @license magnet:?xt=urn:btih:d3d9a9a6595521f9666a5e94cc830dab83b65699&dn=expat.txt MIT

import * as fastboot from "./fastboot/ffe7e270/fastboot.min.mjs";

const RELEASES_URL = "https://releases.grapheneos.org";

const CACHE_DB_NAME = "BlobStore";
const CACHE_DB_VERSION = 1;

const lang = (() => {
    const path = window.location.pathname;
    const match = path.match(/^\/(de|fr|es|ru)\//);
    return match ? match[1] : "en";
})();

const translations = {};

async function loadTranslations() {
    const langFiles = {
        en: "/i18n/en/messages.json",
        de: "/i18n/de/messages.json",
        fr: "/i18n/fr/messages.json",
        es: "/i18n/es/messages.json",
        ru: "/i18n/ru/messages.json"
    };
    
    try {
        const response = await fetch(langFiles[lang] || langFiles.en);
        const data = await response.json();
        
        function flatten(obj, prefix = "") {
            for (const key in obj) {
                if (typeof obj[key] === "object" && obj[key] !== null) {
                    flatten(obj[key], prefix + key + ".");
                } else {
                    translations[prefix + key] = obj[key];
                }
            }
        }
        flatten(data);
    } catch (e) {
        console.warn("Failed to load translations, using defaults:", e);
    }
}

function t(key, params = {}) {
    let text = translations[key] || key;
    for (const [param, value] of Object.entries(params)) {
        text = text.replace(new RegExp(`\\{${param}\\}`, "g"), value);
    }
    return text;
}

loadTranslations();

const Buttons = {
    UNLOCK_BOOTLOADER: "unlock-bootloader",
    DOWNLOAD_RELEASE: "download-release",
    FLASH_RELEASE: "flash-release",
    LOCK_BOOTLOADER: "lock-bootloader",
    REMOVE_CUSTOM_KEY: "remove-custom-key"
};

const InstallerState = {
    DOWNLOADING_RELEASE: 0x1,
    INSTALLING_RELEASE: 0x2
};

let wakeLock = null;

const requestWakeLock = async () => {
    try {
        wakeLock = await navigator.wakeLock.request("screen");
        console.log("Wake lock has been set");
        wakeLock.addEventListener("release", async () => {
            console.log("Wake lock has been released");
        });
    } catch (err) {
        // if wake lock request fails - usually system related, such as battery
        throw new Error(`${err.name}, ${err.message}`);
    }
};

const releaseWakeLock = async () => {
    if (wakeLock !== null) {
        wakeLock.release().then(() => {
            wakeLock = null;
        });
    }
};

// reacquires the wake lock should the visibility of the document change and the wake lock is released
document.addEventListener("visibilitychange", async () => {
    if (wakeLock !== null && document.visibilityState === "visible") {
        await requestWakeLock();
    }
});

// This wraps XHR because getting progress updates with fetch() is overly complicated.
function fetchBlobWithProgress(url, onProgress) {
    let xhr = new XMLHttpRequest();
    xhr.open("GET", url);
    xhr.responseType = "blob";
    xhr.send();

    return new Promise((resolve, reject) => {
        xhr.onload = () => {
            if (xhr.status !== 200) {
                reject(`${xhr.status} ${xhr.statusText}`);
            } else {
                resolve(xhr.response);
            }
        };
        xhr.onprogress = (event) => {
            onProgress(event.loaded / event.total);
        };
        xhr.onerror = () => {
            reject(t("installer.network_error"));
        };
    });
}

function setButtonState({ id, enabled }) {
    const button = document.getElementById(`${id}-button`);
    button.disabled = !enabled;
    return button;
}

class BlobStore {
    constructor() {
        this.db = null;
    }

    async _wrapReq(request, onUpgrade = null) {
        return new Promise((resolve, reject) => {
            request.onsuccess = () => {
                resolve(request.result);
            };
            request.oncomplete = () => {
                resolve(request.result);
            };
            request.onerror = () => {
                reject(request.error);
            };

            if (onUpgrade !== null) {
                request.onupgradeneeded = onUpgrade;
            }
        });
    }

    async _wrapTransaction(transaction) {
        return new Promise((resolve, reject) => {
            transaction.oncomplete = () => {
                resolve(transaction.result);
            };
            transaction.onerror = () => {
                reject(transaction.error);
            };
            transaction.onabort = () => {
                reject(transaction.error);
            };
        });
    }

    async init() {
        if (this.db === null) {
            this.db = await this._wrapReq(
                indexedDB.open(CACHE_DB_NAME, CACHE_DB_VERSION),
                (event) => {
                    let db = event.target.result;
                    db.createObjectStore("files", { keyPath: "name" });
                    /* no index needed for such a small database */
                }
            );
        }
    }

    async saveFile(name, blob) {
        const transaction = this.db.transaction(["files"], "readwrite");
        const request = transaction.objectStore("files").add({
            name: name,
            blob: blob,
        });
        await Promise.all([this._wrapTransaction(transaction), this._wrapReq(request)]);
    }

    async loadFile(name) {
        try {
            let obj = await this._wrapReq(
                this.db.transaction("files").objectStore("files").get(name)
            );
            return obj.blob;
        } catch {
            return null;
        }
    }

    async close() {
        this.db.close();
    }

    async download(url, onProgress = () => {}) {
        let filename = url.split("/").pop();
        let blob = await this.loadFile(filename);
        if (blob === null) {
            console.log(`Downloading ${url}`);
            let blob = await fetchBlobWithProgress(url, onProgress);
            console.log("File downloaded, saving...");
            await this.saveFile(filename, blob);
            console.log("File saved");
        } else {
            console.log(
                `Loaded ${filename} from blob store, skipping download`
            );
        }

        return blob;
    }
}

class ButtonController {
    #map;

    constructor() {
        this.#map = new Map();
    }

    setEnabled(...ids) {
        ids.forEach((id) => {
            // Only enable button if it won't be disabled.
            if (!this.#map.has(id)) {
                this.#map.set(id, /* enabled = */ true);
            }
        });
    }

    setDisabled(...ids) {
        ids.forEach((id) => this.#map.set(id, /* enabled = */ false));
    }

    applyState() {
        this.#map.forEach((enabled, id) => {
            setButtonState({ id, enabled });
        });
        this.#map.clear();
    }
}

let installerState = 0;

let device = new fastboot.FastbootDevice();
let blobStore = new BlobStore();
let buttonController = new ButtonController();

async function ensureConnected(setProgress) {
    if (!device.isConnected) {
        setProgress(t("installer.connecting"));
        await device.connect();
    }
}

async function unlockBootloader(setProgress) {
    await ensureConnected(setProgress);

    if (await device.getVariable("unlocked") === "yes") {
        return t("installer.bootloader_already_unlocked");
    }

    setProgress(t("installer.unlocking"));
    try {
        await device.runCommand("flashing unlock");
    } catch (error) {
        if (error instanceof fastboot.FastbootError && error.status === "FAIL") {
            throw new Error(t("installer.unlock_rejected"));
        } else {
            throw error;
        }
    }

    return t("installer.unlock_success");
}

const supportedDevices = ["rango", "mustang", "blazer", "frankel", "tegu", "comet", "komodo", "caiman", "tokay", "akita", "husky", "shiba", "felix", "tangorpro", "lynx", "cheetah", "panther", "bluejay", "raven", "oriole", "barbet", "redfin", "bramble", "sunfish", "coral", "flame"];

const legacyQualcommDevices = ["sunfish", "coral", "flame"];

const day1SnapshotCancelDevices = ["tegu", "comet", "komodo", "caiman", "tokay", "akita", "husky", "shiba", "felix", "tangorpro", "lynx", "cheetah", "panther", "bluejay", "raven", "oriole", "barbet", "redfin", "bramble"];

function hasOptimizedFactoryImage(product) {
    return !legacyQualcommDevices.includes(product);
}

async function getLatestRelease() {
    let product = await device.getVariable("product");
    if (!supportedDevices.includes(product)) {
        throw new Error(t("installer.device_not_supported", { device: product }));
    }

    let metadataResp = await fetch(`${RELEASES_URL}/${product}-stable`);
    let metadata = await metadataResp.text();
    let releaseId = metadata.split(" ")[0];

    return [`${product}-${hasOptimizedFactoryImage(product) ? "install" : "factory"}-${releaseId}.zip`, product];
}

async function downloadRelease(setProgress) {
    await requestWakeLock();
    await ensureConnected(setProgress);

    setProgress(t("installer.finding_release"));
    let [latestZip,] = await getLatestRelease();

    setInstallerState({ state: InstallerState.DOWNLOADING_RELEASE, active: true });
    setProgress(t("installer.downloading", { filename: latestZip }));
    await blobStore.init();
    try {
        await blobStore.download(`${RELEASES_URL}/${latestZip}`, (progress) => {
            setProgress(t("installer.downloading", { filename: latestZip }), progress);
        });
    } finally {
        setInstallerState({ state: InstallerState.DOWNLOADING_RELEASE, active: false });
        await releaseWakeLock();
    }
    setProgress(t("installer.downloaded", { filename: latestZip }), 1.0);
}

async function reconnectCallback() {
    let statusField = document.getElementById("flash-release-status");
    statusField.textContent = t("installer.reconnect_prompt");

    let reconnectButton = document.getElementById("flash-reconnect-button");
    let progressBar = document.getElementById("flash-release-progress");

    progressBar.hidden = true;
    reconnectButton.hidden = false;

    reconnectButton.onclick = async () => {
        await device.connect();
        reconnectButton.hidden = true;
        progressBar.hidden = false;
    };
}

async function flashRelease(setProgress) {
    await requestWakeLock();
    await ensureConnected(setProgress);

    setProgress(t("installer.finding_release"));
    let [latestZip, product] = await getLatestRelease();
    await blobStore.init();
    let blob = await blobStore.loadFile(latestZip);
    if (blob === null) {
        throw new Error(t("installer.download_first"));
    }

    setProgress(t("installer.cancelling_ota"));
    if (day1SnapshotCancelDevices.includes(product)) {
        let snapshotStatus = await device.getVariable("snapshot-update-status");
        if (snapshotStatus !== null && snapshotStatus !== "none") {
            await device.runCommand("snapshot-update:cancel");
        }
    }

    setProgress(t("installer.flashing"));
    setInstallerState({ state: InstallerState.INSTALLING_RELEASE, active: true });
    try {
        await device.flashFactoryZip(blob, true, reconnectCallback,
            (action, item, progress) => {
                let userAction = fastboot.USER_ACTION_MAP[action];
                let userItem = item === "avb_custom_key" ? "verified boot key" : item;
                setProgress(`${userAction} ${userItem}...`, progress);
            }
        );
        if (legacyQualcommDevices.includes(product)) {
            setProgress(t("installer.disabling_uart"));
            await device.runCommand("oem uart disable ");
            setProgress(t("installer.erasing_apdp"));
            await device.runCommand("erase:apdp_a");
            await device.runCommand("erase:apdp_b");
            setProgress(t("installer.erasing_msadp"));
            await device.runCommand("erase:msadp_a");
            await device.runCommand("erase:msadp_b");
        }
    } finally {
        setInstallerState({ state: InstallerState.INSTALLING_RELEASE, active: false });
        await releaseWakeLock();
    }

    return t("installer.flash_success", { filename: latestZip });
}

async function eraseNonStockKey(setProgress) {
    await ensureConnected(setProgress);

    setProgress(t("installer.erasing_key"));
    try {
        await device.runCommand("erase:avb_custom_key");
    } catch (error) {
        console.log(error);
        throw error;
    }
    return t("installer.key_erased");
}

async function lockBootloader(setProgress) {
    await ensureConnected(setProgress);

    setProgress(t("installer.locking"));
    try {
        await device.runCommand("flashing lock");
    } catch (error) {
        if (error instanceof fastboot.FastbootError && error.status === "FAIL") {
            throw new Error(t("installer.lock_rejected"));
        } else {
            throw error;
        }
    }

    return t("installer.lock_success");
}

function addButtonHook(id, callback) {
    let statusContainer = document.getElementById(`${id}-status-container`);
    let statusField = document.getElementById(`${id}-status`);
    let progressBar = document.getElementById(`${id}-progress`);

    let statusCallback = (status, progress) => {
        if (statusContainer !== null) {
            statusContainer.hidden = false;
        }

        statusField.className = "";
        statusField.textContent = status;

        if (progress !== undefined) {
            progressBar.hidden = false;
            progressBar.value = progress;
        }
    };

    let button = setButtonState({ id, enabled: true });
    button.onclick = async () => {
        try {
            let finalStatus = await callback(statusCallback);
            if (finalStatus !== undefined) {
                statusCallback(finalStatus);
            }
        } catch (error) {
            let errorMessage;
            if (error instanceof DOMException && error.name === "QuotaExceededError") {
                errorMessage = t("installer.quota_warning");
            } else if (typeof(error) === "object" && error.message != null && error.message !== "") {
                errorMessage = error.message;
            } else {
                errorMessage = error.toString();
            }
            statusCallback(`${t("common.error")}: ${errorMessage}`);
            statusField.className = "error-text";
            await releaseWakeLock();
            throw error;
        }
    };
}

function setInstallerState({ state, active }) {
    if (active) {
        installerState |= state;
    } else {
        installerState &= ~state;
    }
    invalidateInstallerState();
}

function isInstallerStateActive(state) {
    return (installerState & state) === state;
}

function invalidateInstallerState() {
    if (isInstallerStateActive(InstallerState.DOWNLOADING_RELEASE)) {
        buttonController.setDisabled(Buttons.DOWNLOAD_RELEASE);
    } else {
        buttonController.setEnabled(Buttons.DOWNLOAD_RELEASE);
    }

    let disableWhileInstalling = [
        Buttons.DOWNLOAD_RELEASE,
        Buttons.FLASH_RELEASE,
        Buttons.LOCK_BOOTLOADER,
        Buttons.REMOVE_CUSTOM_KEY,
    ];
    if (isInstallerStateActive(InstallerState.INSTALLING_RELEASE)) {
        buttonController.setDisabled(...disableWhileInstalling);
    } else {
        buttonController.setEnabled(...disableWhileInstalling);
    }

    buttonController.applyState();
}

function safeToLeave() {
    return installerState === 0;
}

// This doesn't really hurt, and because this page is exclusively for web install,
// we can tolerate extra logging in the console in case something goes wrong.
fastboot.setDebugLevel(2);

fastboot.configureZip({
    workerScripts: {
        inflate: ["/js/fastboot/ffe7e270/vendor/z-worker-pako.js", "pako_inflate.min.js"],
    },
});

if ("usb" in navigator) {
    addButtonHook(Buttons.UNLOCK_BOOTLOADER, unlockBootloader);
    addButtonHook(Buttons.DOWNLOAD_RELEASE, downloadRelease);
    addButtonHook(Buttons.FLASH_RELEASE, flashRelease);
    addButtonHook(Buttons.LOCK_BOOTLOADER, lockBootloader);
    addButtonHook(Buttons.REMOVE_CUSTOM_KEY, eraseNonStockKey);

    if (navigator.storage && navigator.storage.estimate) {
        navigator.storage.estimate().then(estimate => {
            // Currently factory images are ~1700MiB
            // Show a warning if the estimated space is below 2000MiB
            if (estimate.quota !== 0 && estimate.quota < 2000 * 1024 * 1024) {
                document.getElementById("quota-warning-text").hidden = false;
            }
        });
    }
} else {
    console.log("WebUSB unavailable");
    for (const btnId in Buttons) {
        const elementId = Buttons[btnId];
        const statusContainer = document.getElementById(`${elementId}-status-container`);
        const statusField = document.getElementById(`${elementId}-status`);
        if (statusContainer !== null) {
            statusContainer.hidden = false;
        }
        statusField.className = "error-text";
        statusField.innerHTML = t("installer.webusb_unavailable");
    }
}

// This will create an alert box to stop the user from leaving the page during actions
window.addEventListener("beforeunload", event => {
    if (!safeToLeave()) {
        console.log("User tried to leave the page whilst unsafe to leave!");
        event.returnValue = "";
    }
});

// @license-end
