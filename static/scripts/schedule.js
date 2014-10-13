// Global vars
var displayScheduleDate = new Date(device_time); // dk
var displayScheduleTimeout;


function toXSDate(d) {
    var r = d.getFullYear() + "-" +
            (d.getMonth() < 9 ? "0" : "") + (d.getMonth()+1) + "-" +
            (d.getDate() < 10 ? "0" : "") + d.getDate();
    return r;
}

function toClock(duration, tf) {
    var h = Math.floor(duration/60);
    var m = Math.floor(duration - (h*60));
    if (tf == 0) {
        return (h>12 ? h-12 : h) + ":" + (m<10 ? "0" : "") + m + (h<12 ? "am" : "pm");
    } else {
        return (h<10 ? "0" : "") + h + ":" + (m<10 ? "0" : "") + m;
    }
}

function fromClock(clock) {
    var components = clock.split(":");
    var duration = 0;
    for (var c in components) {
        duration = duration*60 + parseInt(components[c], 10);
    }
    return duration;
}

function displaySchedule(schedule) {
    if (displayScheduleTimeout != null) {
        clearTimeout(displayScheduleTimeout);
    }
    var now = new Date((new Date()).getTime() + to_device_time);
    var nowMark = now.getHours()*60 + now.getMinutes();
    var isToday = toXSDate(displayScheduleDate) == toXSDate(now);
    var programClassesUsed = {};
    jQuery(".stationSchedule .scheduleTick").each(function() {
        jQuery(this).empty();
        var sid = jQuery(this).parent().attr("data");
        var slice = parseInt(jQuery(this).attr("data"))*60;
        var boxes = jQuery("<div class='scheduleMarkerContainer'></div>");
        for (var s in schedule) {
            if (schedule[s].station == parseInt(sid, 10)) {
                if (!(isToday && schedule[s].date == undefined && schedule[s].start + schedule[s].duration/60 < nowMark)) {
                    var relativeStart = schedule[s].start - slice;
                    var relativeEnd = schedule[s].start + schedule[s].duration/60 - slice;
                    if (0 <= relativeStart && relativeStart < 60 ||
                        0.05 < relativeEnd && relativeEnd <= 60 ||
                        relativeStart < 0 && relativeEnd >= 60) {
                        var barStart = Math.max(0,relativeStart)/60;
                        var barWidth = Math.max(0.05,Math.min(relativeEnd, 60)/60 - barStart);
                        var programClass;
                        if (schedule[s].manual) {
                            programClass = "programManual";
                        } else {
							programClass = "program" + (parseInt(schedule[s].program)+1)%10;
                        }
                        programClassesUsed[schedule[s].program_name] = programClass;
                        var markerClass = (schedule[s].active == null ? "schedule" : "history");
                        if (schedule[s].blocked) {
                            markerClass = "blocked"
                        }
                        boxes.append("<div class='scheduleMarker " + programClass + " " + markerClass + "' style='left:" + barStart*100 + "%;width:" + barWidth*100 + "%' data='" + schedule[s].program_name + ": " + schedule[s].label + "'></div>");
                    }
                }
            }
        }
        if (isToday && slice <= nowMark && nowMark < slice+60) {
            var stationOn = jQuery(this).parent().children(".stationStatus").hasClass("station_on");
            boxes.append("<div class='nowMarker" + (stationOn?" on":"")+ "' style='width:2px;left:"+ (nowMark-slice)/60*100 + "%;'>");
        }
        if (boxes.children().length > 0) {
            jQuery(this).append(boxes);
        }
    });
    jQuery("#legend").empty();
    for (var p in programClassesUsed) {
        jQuery("#legend").append("<span class='" + programClassesUsed[p] + "'>" + p + "</span>");
    }
    jQuery(".scheduleMarker").mouseover(scheduleMarkerMouseover);
    jQuery(".scheduleMarker").mouseout(scheduleMarkerMouseout);

    jQuery("#displayScheduleDate").text(dateString(displayScheduleDate) + (displayScheduleDate.getFullYear() == now.getFullYear() ? "" : ", " + displayScheduleDate.getFullYear()));
    if (isToday) {
        displayScheduleTimeout = setTimeout(displayProgram, 60*1000);  // every minute
    }
}

function displayProgram() {
    var visibleDate = toXSDate(displayScheduleDate);
    jQuery.getJSON("/api/log?date=" + visibleDate, function(log) {
        for (var l in log) {
            log[l].duration = fromClock(log[l].duration);
            log[l].start = fromClock(log[l].start)/60;
            if (log[l].date != visibleDate) {
                log[l].start -= 24*60;
            }
            if (log[l].blocked) {
                log[l].label = toClock(log[l].start, timeFormat) + " (blocked by " + log[l].blocked + ")";
            } else {
                log[l].label = toClock(log[l].start, timeFormat) + " for " + toClock(log[l].duration, 1);
            }
        }
        displaySchedule(log);
    })
}

jQuery(document).ready(displayProgram);

function scheduleMarkerMouseover() {
    var description = jQuery(this).attr("data");
    var markerClass = jQuery(this).attr("class");
    markerClass = markerClass.substring(markerClass.indexOf("program"));
    markerClass = markerClass.substring(0,markerClass.indexOf(" "));
    jQuery(this).append('<span class="showDetails ' + markerClass + '">' + description + '</span>');
    jQuery(this).children(".showDetails").mouseover(function(){ return false; });
    jQuery(this).children(".showDetails").mouseout(function(){ return false; });
}
function scheduleMarkerMouseout() {
    jQuery(this).children(".showDetails").remove();
}


