package com.amazon.guardrail

import com.intellij.codeInspection.ProblemHighlightType
import com.intellij.json.psi.JsonFile
import com.intellij.psi.FileViewProvider
import com.intellij.psi.PsiFile
import org.mockito.Mockito.mock
import org.mockito.kotlin.whenever
import org.testng.Assert.assertEquals
import org.testng.Assert.assertTrue
import org.testng.annotations.BeforeMethod
import org.testng.annotations.Test

class GuardRailDiagnosticMapperTest {

    private lateinit var mapper: GuardRailDiagnosticMapper
    private lateinit var mockFile: PsiFile

    @BeforeMethod
    fun setup() {
        mapper = GuardRailDiagnosticMapper()
        mockFile = mock(PsiFile::class.java)
    }

    @Test
    fun `mapResults returns empty list for empty JSON`() {
        val result = mapper.mapResults("{}", mockFile)
        assertTrue(result.isEmpty())
    }

    @Test
    fun `mapResults returns empty list for JSON with empty violations`() {
        val cliOutput = """{"non_compliant": {}, "warning": {}}"""
        val result = mapper.mapResults(cliOutput, mockFile)
        assertTrue(result.isEmpty())
    }

    @Test
    fun `mapResults parses single error violation correctly`() {
        val cliOutput = """{
            "non_compliant": {
                "TestRule": [{
                    "check_id": "R001",
                    "message": "Test error",
                    "path": "/properties/test"
                }]
            },
            "warning": {}
        }"""

        val result = mapper.mapResults(cliOutput, mockFile)

        assertEquals(result.size, 1)
        assertEquals(result[0].description, "[R001] Test error")
        assertEquals(result[0].highlightType, ProblemHighlightType.ERROR)
        assertEquals(result[0].ruleName, "TestRule")
        assertEquals(result[0].violation.path, "/properties/test")
    }

    @Test
    fun `mapResults parses single warning violation correctly`() {
        val cliOutput = """{
            "non_compliant": {},
            "warning": {
                "WarningRule": [{
                    "check_id": "W001",
                    "message": "Test warning",
                    "path": "/properties/warn"
                }]
            }
        }"""

        val result = mapper.mapResults(cliOutput, mockFile)

        assertEquals(result.size, 1)
        assertEquals(result[0].description, "[W001] Test warning")
        assertEquals(result[0].highlightType, ProblemHighlightType.WARNING)
        assertEquals(result[0].ruleName, "WarningRule")
    }

    @Test
    fun `mapResults parses multiple violations from same rule`() {
        val cliOutput = """{
            "non_compliant": {
                "Rule1": [
                    {"check_id": "E001", "message": "Error 1", "path": "/path1"},
                    {"check_id": "E002", "message": "Error 2", "path": "/path2"}
                ]
            },
            "warning": {}
        }"""

        val result = mapper.mapResults(cliOutput, mockFile)

        assertEquals(result.size, 2)
        assertEquals(result[0].description, "[E001] Error 1")
        assertEquals(result[1].description, "[E002] Error 2")
    }

    @Test
    fun `mapResults parses violations from multiple rules`() {
        val cliOutput = """{
            "non_compliant": {
                "Rule1": [{"check_id": "E001", "message": "Error 1", "path": "/p1"}],
                "Rule2": [{"check_id": "E002", "message": "Error 2", "path": "/p2"}]
            },
            "warning": {}
        }"""

        val result = mapper.mapResults(cliOutput, mockFile)

        assertEquals(result.size, 2)
        assertTrue(result.any { it.ruleName == "Rule1" })
        assertTrue(result.any { it.ruleName == "Rule2" })
    }

    @Test
    fun `mapResults parses both errors and warnings`() {
        val cliOutput = """{
            "non_compliant": {
                "ErrorRule": [{"check_id": "E001", "message": "Error", "path": "/e"}]
            },
            "warning": {
                "WarnRule": [{"check_id": "W001", "message": "Warning", "path": "/w"}]
            }
        }"""

        val result = mapper.mapResults(cliOutput, mockFile)

        assertEquals(result.size, 2)
        val errors = result.filter { it.highlightType == ProblemHighlightType.ERROR }
        val warnings = result.filter { it.highlightType == ProblemHighlightType.WARNING }
        assertEquals(errors.size, 1)
        assertEquals(warnings.size, 1)
    }

    @Test
    fun `mapResults handles missing fields in violation`() {
        val cliOutput = """{
            "non_compliant": {
                "Rule": [{"check_id": "E001"}]
            },
            "warning": {}
        }"""

        val result = mapper.mapResults(cliOutput, mockFile)

        assertEquals(result.size, 1)
        assertEquals(result[0].description, "[E001] ")
    }

    @Test
    fun `extractLineNumber returns 0 for non-JsonFile`() {
        val lineNumber = mapper.extractLineNumber("/properties/test", mockFile)
        assertEquals(lineNumber, 0)
    }

    @Test
    fun `extractLineNumber returns 0 for empty path`() {
        val lineNumber = mapper.extractLineNumber("", mockFile)
        assertEquals(lineNumber, 0)
    }

    @Test
    fun `extractLineNumber returns 0 when document is null`() {
        val mockJsonFile = mock(JsonFile::class.java)
        val mockViewProvider = mock(FileViewProvider::class.java)

        whenever(mockJsonFile.viewProvider).thenReturn(mockViewProvider)
        whenever(mockViewProvider.document).thenReturn(null)

        val lineNumber = mapper.extractLineNumber("/properties/test", mockJsonFile)
        assertEquals(lineNumber, 0)
    }
}
