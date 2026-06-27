sudo cp org.wakepc.plist /Library/LaunchDaemons/
sudo chown root:wheel /Library/LaunchDaemons/org.wakepc.plist
sudo chmod 644 /Library/LaunchDaemons/org.wakepc.plist
plutil -lint /Library/LaunchDaemons/org.wakepc.plist
sudo launchctl bootstrap system /Library/LaunchDaemons/org.wakepc.plist
