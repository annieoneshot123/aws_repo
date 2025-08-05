graph TD
    subgraph "Internet"
        User[<i class='fa fa-user'></i> Users]
    end

    subgraph "AWS Cloud"
        CloudFront[<i class='fa fa-cloud'></i> CloudFront Distribution]
        ALB[<i class='fa fa-server'></i> Application Load Balancer]

        subgraph "VPC: photoshare-vpc"
            subgraph "Public Subnet (us-east-1a)"
                NATgw1a[<i class='fa fa-route'></i> NAT Gateway 1a]
            end
            subgraph "Public Subnet (us-east-1b)"
                NATgw1b[<i class='fa fa-route'></i> NAT Gateway 1b]
            end

            IGW[<i class='fa fa-globe'></i> Internet Gateway]
            ALB -- Route 53 (Optional) --> User
            User -- HTTP/HTTPS --> ALB

            subgraph "Auto Scaling Group"
                subgraph "Private Subnet (us-east-1a)"
                    EC2_1a[<i class='fa fa-desktop'></i> EC2 Instance 1a]
                end
                subgraph "Private Subnet (us-east-1b)"
                    EC2_1b[<i class='fa fa-desktop'></i> EC2 Instance 1b]
                end
            end
            
            subgraph "RDS Multi-AZ"
                RDS_Master[<i class='fa fa-database'></i> RDS Master (us-east-1a)]
                RDS_Slave[<i class='fa fa-database'></i> RDS Slave (us-east-1b)]
            end

            S3[<i class='fa fa-hdd'></i> S3 Bucket]
        end
    end
    
    User -- Upload Photos --> ALB
    ALB -- Distribute Traffic --> EC2_1a
    ALB -- Distribute Traffic --> EC2_1b

    EC2_1a -- Read/Write Metadata --> RDS_Master
    EC2_1b -- Read/Write Metadata --> RDS_Master
    EC2_1a -- Upload Photos --> S3
    EC2_1b -- Upload Photos --> S3
    
    User -- Request View Photos --> CloudFront
    CloudFront -- Fetch Photos (if cache miss) --> S3
    
    RDS_Master -.-> RDS_Slave
    EC2_1a -- Internet Out --> NATgw1a --> IGW
    EC2_1b -- Internet Out --> NATgw1b --> IGW

    style User fill:#f9f,stroke:#333,stroke-width:2px
    style CloudFront fill:#FF9900,stroke:#333,stroke-width:2px
    style ALB fill:#FF9900,stroke:#333,stroke-width:2px
    style EC2_1a fill:#FF9900,stroke:#333,stroke-width:2px
    style EC2_1b fill:#FF9900,stroke:#333,stroke-width:2px
    style RDS_Master fill:#0073BB,stroke:#333,stroke-width:2px
    style RDS_Slave fill:#0073BB,stroke:#333,stroke-width:2px
    style S3 fill:#E45C56,stroke:#333,stroke-width:2px