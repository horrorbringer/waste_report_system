# Storage

## GraphQL Gateway Setup

---

```json
https://cloudgateway.sabay.com/graphql
```

## **Headers**

---

<aside>

**service-code**

**Authorization**

cloud_user

Bearer `{token}`

</aside>

### Description

   **S3** (Simple Storage Service) is a scalable, durable, and secure cloud storage service designed for storing and retrieving any amount of data, such as files, backups, or media.

## **1. Create Bucket**

  The **s3_createBucket** mutation is used to create a s3. Below are the required fields and their

descriptions.

### **Arguments (**s3_BucketInput)

<aside>

- **input**: (Object, required)
    - **name**: (String, required) The name of the bucket and it is unique across s3.
    - **projectName** : (String, required) The name of the project.
</aside>

**Sample variable**

```json
{
  "input": {
    "bucketName": "bucket03",
    "projectName": "Sell-Product Project"
  }
}
```

### Request:

```graphql
mutation S3_createBucket($input: s3_BucketInput!) {
  s3_createBucket(input: $input) {
   id
   name
   projectName
   url
  }
}
```

### Example Response:

```graphql
{
  "data": {
    "s3_createBucket": {
      "id": "68b571f65f34c302831d923f",
      "name": "bucket03",
      "projectName": "Sell-Product Project"
      "url": "https://fsgw.sabay.test/bucket03"
    }
  }
}
```

## **2. List Bucket**

  The **s3_getUserBuckets** query is used to show bucket lists. Below are the request and example response.

### Request:

```graphql
query getBucketList {
    s3_getUserBuckets {
      bucketList {
        id
        name
        url
        projectName
      }
    }
  }
```

### Example Response:

```graphql
{
  "data": {
    "s3_getUserBuckets": {
      "bucketList": [
       {
          "id": "68b571f65f34c302831d923f",
          "name": "bucket03",
          "url": "https://fsgw.sabay.test/bucket03",
          "projectName": "Sell-Product Project"
        }
      ]
    }
  }
}
```

## **3. Delete Bucket**

  The **s3_deleteBucket** mutation is used to delete a bucket. Below are the required fields and their descriptions.

### **Arguments**

<aside>

- **input**: (Object, required) Contains the details needed to create the bucket.
    - **bucketName**: (String, required) The name of the bucket.
    - **projectName** : (String, required) The name of the project.
</aside>

**Sample variable**

```json
{
  "input": {
    "bucketName": "bucket03",
    "projectName": "Sell-Product Project"
  }
}
```

### Request:

```graphql
mutation deleteS3Bucket($input: s3_BucketInput!) {
    s3_deleteBucket(input: $input) {
      message
      success
    }
  }
```

### Example Response:

```graphql
{
    "data": {
        "s3_deleteBucket": {
            "message": "Bucket deleted successfully",
            "success": true
        }
    }
}
```

## **4. Get Access Key & Secret Key**

  The **s3_getUserDetail** query is used to get access key and secret key. Below are the required fields and their descriptions.

### Request:

```graphql
query getS3UserDetail {
    s3_getUserDetail {
      accessKey
      id
      mysabayUserId
      secretKey
      status
      uid
    }
  }
```

### Example Response:

```graphql
{
    "data": {
        "s3_getUserDetail": {
            "accessKey": "AYKR815PPJ3GWG8XCY0T",
            "id": "668398e9645beaf62d4e0f22",
            "mysabayUserId": 39555695,
            "secretKey": "6mgrX5CfNwCBXgQzZDPNsDbAbq9XcQ8l2Qt2vn3H",
            "status": 1,
            "uid": "39555695",
        }
    }
}
```

## **5. Reset User Key Bucket**

  The **s3_resetUserKey** mutation is used to reset user key. Below are the required fields and their

descriptions.

### Request:

```graphql
mutation resetUserKey {
    s3_resetUserKey {
      message
      success
    }
  }
```

### Example Response:

```graphql
{
    "data": {
        "s3_resetUserKey": {
            "message": "Generate new credential successfully",
            "success": true
        }
    }
}
```

## **6. Project Name**

  The **s3_getUserProject** query is used to get project name. Below are the required fields and their descriptions.

### Request:

```graphql
query getS3UserProject {
    s3_getUserProject {
      mysabayUserId
      id
      projectName
    }
  }
```

### Example Response:

```graphql
{
    "data": {
        "s3_getUserProject": {
            "mysabayUserId": 39555695,
            "id": "668399575535cd7a8efcbc9f",
            "projectName": "Sell-Product Project"
        }
    }
}
```

## **7. Bucket Usage**

  The **sb_summaryUsageByUser** query is used to get usage summary bucket. Below are the required fields and their descriptions.

### **Arguments**

<aside>

- **filter** (Object, required)
    - **subscriptionId**: (String, required) The name of the usage.
    - **serviceCode** : (String, required) The name of the usage.
    - **usageDate** (Object, optional)
        - **startDate** : (String, required) The start date of the usage.
        - **endDate** : (String, required) The end date of the usage.
</aside>

**Sample variable**

```json
{
  "filter": {
    "subscriptionId": "668398e88c6179ed139a19b7",
    "serviceCode": "cloud_s3",
    "usageDate": {
      "startDate": "2024-01-01",
      "endDate": "2024-02-01" 
    },
  }
}
```

### Request:

```graphql
 query sbGetListUsageSummaryByUser($filter: sb_FilterSummaryInput!) {
    sb_summaryUsageByUser(filter: $filter) {
    totalNetwork
    totalStorage
    }
  }
```

### Example Response:

```graphql
{
  "data": {
    "sb_summaryUsageByUser": {
      "totalNetwork": 0,
      "totalStorage": 0
    }
  }
}
```