import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs

ApplicationWindow {
    visible: true
    width: 800
    height: 600
    title: "DICOM Viewer"
    property QtObject backend

    FileDialog {
        id: fileDialog
        title: "Open DICOM File"
        nameFilters: ["DICOM Files (*.dcm)"]
        onAccepted: {
            backend.loadDicom(fileDialog.fileUrl.toString().substring(8))  // Remove "file://"
        }
    }

    Rectangle {
        anchors.fill: parent
        color: "black"

        Image {
            id: dicomImage
            anchors.centerIn: parent
            fillMode: Image.PreserveAspectFit
        }

        Button {
            text: "Open DICOM File"
            anchors.bottom: parent.bottom
            anchors.horizontalCenter: parent.horizontalCenter
            onClicked: fileDialog.open()
        }
    }

    Connections {
        target: backend
        onImageChanged: {
            dicomImage.source = msg
        }
    }
}
