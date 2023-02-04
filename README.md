A wxpython application to set the date, time, timezone and ntp server.

Prerequisites:
python3
wxpython
timedatectl command

The application initially uses the timedatectl command to retrieve the timezone.
If the command fails for any reason whatsoever, the application ends.
A message is issued that date and time cannot be adjusted and to contact the system administrator.

The application verifies if an internet connection exists by trying to contact https://gist.github.com.
If an internet connection exists, 3 sync methods are available: Hardware clock, NTP server and Timezone.
If an internet connection does not exist, 2 sync methods are available: Hardware clock and Timezone.
