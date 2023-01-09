# Flipper Zero Update Indexer and Uploader

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
