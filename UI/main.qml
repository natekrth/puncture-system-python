import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs

ApplicationWindow {
    visible: true
    width: 800
    height: 600
    title: "Raw Image Viewer"
    property QtObject backend

    FileDialog {
        id: fileDialog
        title: "Open Raw Image File"
        nameFilters: ["Raw Files (*.raw)"]
        onAccepted: {
            var fileUrl = fileDialog.fileUrl
            if (fileUrl !== null && fileUrl !== undefined) {
                backend.loadRaw(fileUrl.toString().substring(8), 256, 256);  // Example width and height
            } else {
                console.log("No file selected.");
            }
        }
    }

    Rectangle {
        anchors.fill: parent
        color: "white"

        Image {
            id: rawImage
            anchors.centerIn: parent
            fillMode: Image.PreserveAspectFit
        }

        Button {
            text: "Open Raw Image File"
            anchors.bottom: parent.bottom
            anchors.horizontalCenter: parent.horizontalCenter
            onClicked: fileDialog.open()
        }
    }

    Connections {
        target: backend
        function onImageChanged(msg) {
            console.log("Image changed:", msg);
            rawImage.source = msg;
        }
    }
}
