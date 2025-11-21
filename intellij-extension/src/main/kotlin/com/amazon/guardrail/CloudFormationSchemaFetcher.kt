package com.amazon.guardrail

import com.google.gson.JsonParser
import com.intellij.openapi.diagnostic.Logger
import software.amazon.awssdk.regions.Region
import software.amazon.awssdk.services.cloudformation.CloudFormationClient
import software.amazon.awssdk.services.cloudformation.model.DescribeTypeRequest
import software.amazon.awssdk.services.cloudformation.model.RegistryType
import java.io.File

/**
 * Fetches CloudFormation resource type schemas using the AWS CloudFormation API.
 * 
 * This class reads the typeName from a local schema file and uses the CloudFormation
 * DescribeType API to fetch the registered schema from AWS.
 */
class CloudFormationSchemaFetcher {
    
    private val LOG = Logger.getInstance(CloudFormationSchemaFetcher::class.java)
    
    // Fetches the schema for a resource type from CloudFormation.
    fun fetchSchema(schemaFilePath: String, region: String = "us-east-1"): String? {
        LOG.info("Fetching schema from CloudFormation | File: $schemaFilePath | Region: $region")
        try {
            // get typeName from local schema file
            val typeName = extractTypeName(schemaFilePath)
            if (typeName == null) {
                LOG.error("Failed to extract typeName from schema file: $schemaFilePath")
                return null
            }
            val cfnClient = CloudFormationClient.builder()
                .region(Region.of(region))
                .build()
            
            val request = DescribeTypeRequest.builder()
                .type(RegistryType.RESOURCE)
                .typeName(typeName)
                .build()
            
            LOG.info("Calling CloudFormation DescribeType API for: $typeName")
            
            val response = cfnClient.describeType(request)
            val schema = response.schema()
            
            if (schema != null) {
                LOG.info("Successfully fetched schema from CloudFormation | Length: ${schema.length}")
                return schema
            } else {
                LOG.warn("DescribeType returned null schema for: $typeName")
                return null
            }
            
        } catch (e: Exception) {
            LOG.error("Error fetching schema from CloudFormation", e)
            return null
        }
    }

    private fun extractTypeName(filePath: String): String? {
        return try {
            val fileContent = File(filePath).readText()
            val jsonObject = JsonParser.parseString(fileContent).asJsonObject
            
            if (jsonObject.has("typeName")) {
                jsonObject.get("typeName").asString
            } else {
                LOG.warn("Schema file does not contain 'typeName' field: $filePath")
                null
            }
        } catch (e: Exception) {
            LOG.error("Error reading typeName from file: $filePath", e)
            null
        }
    }
}
