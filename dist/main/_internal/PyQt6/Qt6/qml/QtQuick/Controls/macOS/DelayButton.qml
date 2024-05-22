// Copyright (C) 2023 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Controls.impl
import QtQuick.Templates as T
import QtQuick.NativeStyle as NativeStyle

T.DelayButton {
    id: control

    readonly property bool __nativeBackground: background instanceof NativeStyle.StyleItem
    readonly property bool __notCustomizable: true
    readonly property Item __focusFrameTarget: control

    implicitWidth: Math.max(implicitBackgroundWidth + leftInset + rightInset,
                            implicitContentWidth + leftPadding + rightPadding)
    implicitHeight: Math.max(implicitBackgroundHeight + topInset + bottomInset,
                             implicitContentHeight + topPadding + bottomPadding)

    leftPadding: __nativeBackground ? background.contentPadding.left : 5
    rightPadding: __nativeBackground ? background.contentPadding.right : 5
    topPadding: __nativeBackground ? background.contentPadding.top : 5
    bottomPadding: __nativeBackground ? background.contentPadding.bottom : 5

    background: NativeStyle.DelayButton {
        control: control
        contentWidth: control.contentItem.implicitWidth
        contentHeight: control.contentItem.implicitHeight

        readonly property bool __ignoreNotCustomizable: true
    }

    icon.width: 24
    icon.height: 24
    icon.color: control.palette.buttonText

    transition: Transition {
        NumberAnimation {
            duration: control.delay * (control.pressed ? 1.0 - control.progress : 0.3 * control.progress)
        }
    }

    contentItem: IconLabel {
        spacing: control.spacing
        mirrored: control.mirrored
        display: control.display

        icon: control.icon
        text: control.text
        font: control.font
        color: control.palette.buttonText

        readonly property bool __ignoreNotCustomizable: true

        // Delay progress bar.
        Rectangle {
            x: (parent.width - parent.implicitWidth) / 2
            y: parent.height + (Qt.styleHints.colorScheme === Qt.Light ? 1 : 0)
            width: control.progress * parent.implicitWidth
            // The bar is too thick for the light theme at 2 pixels,
            // but too thin for the dark theme at 1.
            height: Qt.styleHints.colorScheme === Qt.Light ? 1 : 2
            color: control.palette.accent
            scale: control.mirrored ? -1 : 1
        }
    }
}
