# Flipper Zero Update Indexer and Uploader

## Start localy
```bash
    INDEXER_FIRMWARE_GITHUB_TOKEN= \
    INDEXER_QFLIPPER_GITHUB_TOKEN= \
    INDEXER_GITHUB_ORGANIZATION= \
    INDEXER_QFLIPPER_GITHUB_REPO= \
    INDEXER_FIRMWARE_GITHUB_REPO= \
    INDEXER_BLACKMAGIC_GITHUB_TOKEN= \
    INDEXER_BLACKMAGIC_GITHUB_REPO= \
    INDEXER_TOKEN= \
    INDEXER_BASE_URL= \
    INDEXER_FILES_DIR= \
    make run
```

Clearing:
```bash
    make clean
```

## Requests example
Get index
```bash
    curl 127.0.0.1:8000/firmware/directory.json
```

Get latest release
```bash
    # format: 127.0.0.1:8000/{directory}/{channel}/{target}/{type}
    # if target contains '/' (slash) replace it by '-' dash symbol
    curl 127.0.0.1:8000/firmware/release/f7/updater_json
    curl 127.0.0.1:8000/qFlipper/release/windows-amd64/installer
```

Trigger reindex
```bash
    curl -H "Token: YOUR_TOKEN" 127.0.0.1:8000/firmware/reindex
```

Upload files
```bash
    curl -L -H "Token: YOUR_TOKEN" \
        -F "branch=drunkbatya/test-spimemmanager" \
        -F "files=@flipper-z-any-core2_firmware-0.73.1.tgz" \
        -F "files=@flipper-z-f7-full-0.73.1.json" \
        127.0.0.1:8000/firmware/uploadfiles
```
