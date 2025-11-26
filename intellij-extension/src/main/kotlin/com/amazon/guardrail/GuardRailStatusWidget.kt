package com.amazon.guardrail

import com.intellij.openapi.project.Project
import com.intellij.openapi.wm.StatusBar
import com.intellij.openapi.wm.StatusBarWidget
import com.intellij.openapi.wm.StatusBarWidget.TextPresentation
import com.intellij.util.Consumer
import java.awt.event.MouseEvent

/**
 * Status bar widget that displays Guard Rail validation summary.
 * * This widget shows:
 * - Green success indicator when no issues found
 * - Red background with error count when errors present
 * - Yellow background with warning count when only warnings present
 * - Both counts when errors and warnings present
 * * The widget also provides a tooltip with detailed validation status.
 */
class GuardRailStatusWidget(private val project: Project) : StatusBarWidget {

    private var statusBar: StatusBar? = null

    @Volatile
    private var errorCount: Int = 0

    @Volatile
    private var warningCount: Int = 0

    private val presentation = MyTextPresentation()

    companion object {
        const val ID = "GuardRailStatusWidget"
    }

    override fun ID(): String = ID

    override fun getPresentation(): StatusBarWidget.WidgetPresentation = presentation

    private inner class MyTextPresentation : TextPresentation {
        override fun getText(): String {
            return when {
                errorCount > 0 && warningCount > 0 -> "Guard Rail: $errorCount errors, $warningCount warnings"
                errorCount > 0 -> "Guard Rail: $errorCount errors"
                warningCount > 0 -> "Guard Rail: $warningCount warnings"
                else -> "Guard Rail: ✓"
            }
        }

        override fun getAlignment(): Float = 0.0f

        override fun getTooltipText(): String {
            return when {
                errorCount > 0 && warningCount > 0 -> "Guard Rail validation found $errorCount error(s) and $warningCount warning(s)"
                errorCount > 0 -> "Guard Rail validation found $errorCount error(s)"
                warningCount > 0 -> "Guard Rail validation found $warningCount warning(s)"
                else -> "Guard Rail validation passed with no issues"
            }
        }

        override fun getClickConsumer(): Consumer<MouseEvent>? = null
    }

    override fun install(statusBar: StatusBar) {
        this.statusBar = statusBar
    }

    override fun dispose() {
        statusBar = null
    }

    fun updateStatus(errorCount: Int, warningCount: Int) {
        this.errorCount = errorCount
        this.warningCount = warningCount

        // Trigger widget refresh
        statusBar?.updateWidget(ID)
    }
}
