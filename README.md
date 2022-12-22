# Flipper Zero Update Indexer and Uploader

## Requests example
Get index
```bash
    curl 127.0.0.1:8000/firmware/directory.json
```

Trigger reindex
```bash
    curl -H "Token: YOUR_TOKEN" 127.0.0.1:8000/reindex
```

Upload files
```bash
    curl -L -H "Token: YOUR_TOKEN" \
        -F "branch=drunkbatya/test-spimemmanager" \
        -F "files=@flipper-z-any-core2_firmware-0.73.1.tgz" \
        -F "files=@flipper-z-f7-full-0.73.1.json" \
        127.0.0.1:8000/firmware/uploadfiles
```
