package com.amazon.guardrail

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder
import org.mockito.Mockito.mock
import org.mockito.kotlin.any
import org.mockito.kotlin.whenever
import software.amazon.awssdk.regions.Region
import software.amazon.awssdk.services.cloudformation.CloudFormationClient
import software.amazon.awssdk.services.cloudformation.model.DescribeTypeRequest
import software.amazon.awssdk.services.cloudformation.model.DescribeTypeResponse

class CloudFormationSchemaFetcherTest {

    @get:Rule
    val tempFolder = TemporaryFolder()

    private lateinit var mockClient: CloudFormationClient
    private lateinit var fetcher: CloudFormationSchemaFetcher

    @Before
    fun setup() {
        mockClient = mock(CloudFormationClient::class.java)
        fetcher = CloudFormationSchemaFetcher { mockClient }
    }

    @Test
    fun `extractTypeName returns null when typeName field is missing`() {
        val file = tempFolder.newFile("no-typename.json")
        file.writeText("""{"properties": {}}""")

        val result = fetcher.extractTypeName(file.absolutePath)
        assertNull(result)
    }

    @Test
    fun `extractTypeName extracts typeName from valid schema`() {
        val file = tempFolder.newFile("valid.json")
        file.writeText("""{"typeName": "AWS::S3::Bucket"}""")

        val result = fetcher.extractTypeName(file.absolutePath)
        assertEquals("AWS::S3::Bucket", result)
    }

    @Test
    fun `extractTypeName handles complex typeName`() {
        val file = tempFolder.newFile("complex.json")
        file.writeText("""{"typeName": "AWS::EC2::Instance", "properties": {"foo": "bar"}}""")

        val result = fetcher.extractTypeName(file.absolutePath)
        assertEquals("AWS::EC2::Instance", result)
    }

    @Test
    fun `fetchSchema returns schema from CloudFormation API`() {
        val file = tempFolder.newFile("schema.json")
        file.writeText("""{"typeName": "AWS::S3::Bucket"}""")

        val mockResponse = mock(DescribeTypeResponse::class.java)
        whenever(mockResponse.schema()).thenReturn("""{"type": "object"}""")
        whenever(mockClient.describeType(any<DescribeTypeRequest>())).thenReturn(mockResponse)

        val result = fetcher.fetchSchema(file.absolutePath)

        assertEquals("""{"type": "object"}""", result)
    }

    @Test
    fun `fetchSchema returns null when CloudFormation returns null schema`() {
        val file = tempFolder.newFile("schema.json")
        file.writeText("""{"typeName": "AWS::Custom::Resource"}""")

        val mockResponse = mock(DescribeTypeResponse::class.java)
        whenever(mockResponse.schema()).thenReturn(null)
        whenever(mockClient.describeType(any<DescribeTypeRequest>())).thenReturn(mockResponse)

        val result = fetcher.fetchSchema(file.absolutePath)

        assertNull(result)
    }

    @Test
    fun `fetchSchema uses correct region`() {
        val file = tempFolder.newFile("schema.json")
        file.writeText("""{"typeName": "AWS::S3::Bucket"}""")

        var capturedRegion: Region? = null
        val customFetcher = CloudFormationSchemaFetcher { region ->
            capturedRegion = region
            mockClient
        }

        val mockResponse = mock(DescribeTypeResponse::class.java)
        whenever(mockResponse.schema()).thenReturn("""{"type": "object"}""")
        whenever(mockClient.describeType(any<DescribeTypeRequest>())).thenReturn(mockResponse)

        customFetcher.fetchSchema(file.absolutePath, "eu-west-1")

        assertEquals(Region.EU_WEST_1, capturedRegion)
    }

    @Test
    fun `fetchSchema handles multiple resource types`() {
        val file1 = tempFolder.newFile("s3.json")
        file1.writeText("""{"typeName": "AWS::S3::Bucket"}""")

        val file2 = tempFolder.newFile("ec2.json")
        file2.writeText("""{"typeName": "AWS::EC2::Instance"}""")

        val mockResponse = mock(DescribeTypeResponse::class.java)
        whenever(mockResponse.schema()).thenReturn("""{"type": "object"}""")
        whenever(mockClient.describeType(any<DescribeTypeRequest>())).thenReturn(mockResponse)

        val result1 = fetcher.fetchSchema(file1.absolutePath)
        val result2 = fetcher.fetchSchema(file2.absolutePath)

        assertEquals("""{"type": "object"}""", result1)
        assertEquals("""{"type": "object"}""", result2)
    }
}
