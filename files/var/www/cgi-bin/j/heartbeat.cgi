#!/bin/sh
# shellcheck disable=SC2039

vendor=$(ipcinfo --vendor)

soc_temp=$(ipcinfo --temp 2>/dev/null)
if [ -n "$soc_temp" ]; then
	soc_temp="${soc_temp}°C"
else
	soc_temp=""
fi

if pidof majestic; then
	daynight_value=$(timeout .5 wget -q -O - http://127.0.0.1/metrics?value=isp_again)
	if [ -z "$daynight_value" ]; then
		daynight_value=-1
	fi
fi

if [ -z "$daynight_value" ]; then
	case "$vendor" in
		ingenic)
			daynight_value=$(imp-control.sh gettotalgain)
			;;
		sigmastar)
			if [ -e /sys/devices/virtual/mstar/sar/channel ]; then
				echo 2 >/sys/devices/virtual/mstar/sar/channel
				daynight_value=$(cat /sys/devices/virtual/mstar/sar/value)
			else
				daynight_value=-1
			fi
			;;
		*)
			daynight_value=-1
			;;
	esac
fi

mem_total=$(awk '/MemTotal/ {print $2}' /proc/meminfo)
mem_free=$(awk '/MemFree/ {print $2}' /proc/meminfo)
mem_used=$(( 100 - (mem_free / (mem_total / 100)) ))
overlay_used=$(df | grep /overlay | xargs | cut -d' ' -f5)
uptime=$(awk '{m=$1/60; h=m/60; printf "%sd %sh %sm %ss\n", int(h/24), int(h%24), int(m%60), int($1%60) }' /proc/uptime)
payload=$(printf '{"soc_temp":"%s","time_now":"%s","timezone":"%s","mem_used":"%d","overlay_used":"%d","daynight_value":"%d","uptime":"%s"}' \
 	"$soc_temp" "$(date +%s)" "$(cat /etc/timezone)" "$mem_used" "${overlay_used//%/}" "$daynight_value", "$uptime")

echo "HTTP/1.1 200 OK
Content-type: application/json
Pragma: no-cache
Expires: $(TZ=GMT0 date +'%a, %d %b %Y %T %Z')
Etag: \"$(cat /proc/sys/kernel/random/uuid)\"

${payload}
"
