# Kronos - AWS Static Site Hosting

**Taking a university web project and deploying it on real AWS infrastructure using S3, CloudFront and IAM.**

> Quick note before anything else: this project isn't really about the website. Kronos (a fictional luxury watch store) was built for a university Web Development module. What this README is actually about is what I did *after* that: I took the finished site and used it to practice real AWS skills. So the focus here is the cloud infrastructure, not the front-end code.

## Architecture

![Architecture diagram](screenshots/00-architecture-diagram.png)

Here's how a request actually travels through the system: a browser asks for the site, Route 53 isn't used in this version (I kept things simple and used the CloudFront domain directly), CloudFront handles the request with HTTPS and caching, and only CloudFront is allowed to read from the S3 bucket where the files actually live.

The bucket itself is completely private. You can't open it directly, not even by guessing the URL. I tested this on purpose, more on that below.

## AWS services used

| Service | What it does here |
|---|---|
| AWS CLI | Used to check my setup and confirm which IAM user I was working as |
| IAM | A dedicated CLI user with limited permissions, plus a separate admin user with MFA, instead of using the root account |
| S3 | Hosts the actual website files, kept fully private |
| CloudFront | Sits in front of S3, adds HTTPS and caching, and is the only thing allowed to reach the bucket (via Origin Access Control) |
| AWS WAF | Basic managed protection attached to CloudFront |

I looked into adding a custom domain through Route 53 but decided to skip it for this version. It's something I can add later without changing anything else I built here.

## Step 1: setting up IAM first

Before touching S3 or CloudFront, I set up IAM properly. I didn't want to just use the root account for everything, which is what a lot of beginners do without thinking about it.

I created two separate users:

- `adrian-cli-kronos`, only used for the AWS CLI on my laptop. It has no console password, just permissions for S3 and CloudFront.
- `adrian-admin`, which I actually log into the console with. It has a password and MFA turned on (using an authenticator app on my phone).

![IAM user created](screenshots/01-iam-user-created.png)
![IAM users list](screenshots/01b-iam-user-list.png)
![MFA enabled](screenshots/02-mfa-enabled.png)

Then I installed the AWS CLI locally and connected it to the CLI user:

```
aws configure
aws sts get-caller-identity
```

![CLI verified](screenshots/03-cli-verified.png)

The reason I did it this way: if the root account's credentials ever leaked, someone would have full control over everything. A limited user for CLI work and a separate admin account with MFA means the blast radius of any mistake is much smaller. It's a small extra step at the start but it's worth it.

## Step 2: the S3 bucket

I created a bucket called `kronos-aws-project-2026` and turned on static website hosting, with `index.html` set as the index document. Block Public Access stayed switched on the whole time. I never opened the bucket up to the public directly.

![Bucket created](screenshots/04-bucket-created.png)

### A problem I ran into with the file structure

My project had all the HTML pages sitting inside a `Pages/` folder, which made sense for the GitHub repo from the university assignment. When I uploaded everything to S3 exactly like that, the site didn't load. S3 looks for `index.html` at the root of the bucket, not inside a subfolder, so it just couldn't find it.

What I did to fix it: I uploaded the HTML files both inside `Pages/` (keeping the original structure) and again directly at the root, next to `css/`, `js/` and `media/`. A bit of duplication, but it meant the site worked from the root while I still kept the folder structure I already had.

![Upload succeeded](screenshots/04b-upload-succeeded.png)

## Step 3: CloudFront

Next I created a CloudFront distribution pointing at the S3 bucket, with a few settings I want to explain:

- Origin access: I used Origin Access Control, which lets CloudFront read from the bucket without the bucket being public.
- Viewer protocol policy: redirect HTTP to HTTPS.
- Default root object: `index.html`.
- AWS WAF: turned on with the default managed rules.

![CloudFront review before create](screenshots/05b-cloudfront-review.png)
![CloudFront distribution created](screenshots/05-cloudfront-created.png)

### Why I didn't use the S3 website endpoint

AWS actually suggests using the S3 website endpoint when static hosting is turned on, it's simpler and supports some extra features like custom error pages. I went against that on purpose. The website endpoint only works if the bucket is fully public, and that doesn't work with Origin Access Control. Since keeping the bucket private was the whole point of this setup, I used the regular S3 endpoint instead and accepted losing a couple of convenience features.

### The bucket policy CloudFront wrote automatically

```json
{
  "Sid": "AllowCloudFrontServicePrincipal",
  "Effect": "Allow",
  "Principal": { "Service": "cloudfront.amazonaws.com" },
  "Action": "s3:GetObject",
  "Resource": "arn:aws:s3:::kronos-aws-project-2026/*",
  "Condition": {
    "ArnLike": {
      "AWS:SourceArn": "arn:aws:cloudfront::[account-id]:distribution/[distribution-id]"
    }
  }
}
```

![Bucket policy](screenshots/06-bucket-policy.png)

This only allows reading files (`s3:GetObject`, nothing else), and only when the request comes from this exact CloudFront distribution, not from CloudFront in general and definitely not from anyone else.

### About AWS WAF

I almost skipped WAF entirely because it has a small monthly cost per Web ACL even with no traffic. I had AWS credit available and the cost for a project this size was basically nothing, so I turned it on mainly to show I understand what it does and when it's worth using. If I didn't have credit, I probably would have left it off for a test project like this.

## Step 4: testing it actually works

### The site loads through CloudFront

![Site working via CloudFront](screenshots/07-site-live.png)

### Testing that the bucket really is private

I wanted to actually prove the security setup worked instead of just trusting the settings screen, so I tried opening a file directly through the S3 URL instead of going through CloudFront:

```
https://kronos-aws-project-2026.s3.eu-west-2.amazonaws.com/index.html
```

What came back:

```xml
<Error>
  <Code>AccessDenied</Code>
  <Message>Access Denied</Message>
</Error>
```

![Access denied on direct S3 access](screenshots/08-access-denied.png)

That confirmed the bucket really can't be reached on its own. CloudFront is the only way in.

## Cost

Everything here stayed inside AWS Free Tier, using AWS credit I had on the account. Building, testing and then tearing it all down cost less than a dollar total, WAF included.

## Tearing it down

Once I had all the screenshots and the site was confirmed working, I deleted everything to avoid ongoing charges:

1. Disabled the CloudFront distribution, then deleted it once it finished deploying.
2. Emptied the S3 bucket, then deleted it.
3. Checked that the WAF Web ACL was gone too (it got removed automatically along with CloudFront).
4. Kept the IAM users since they don't cost anything and I'll reuse a similar setup for the next project.

Nothing from this project is still live. Everything above is proof it worked while it was up.

## What I actually learned

- How Origin Access Control works and why it's meaningfully more secure than a public bucket, and that it's worth testing the restriction directly instead of just assuming the console settings did what they say.
- Why the S3 REST endpoint and the S3 website endpoint aren't the same thing once you care about security, since only one of them supports OAC.
- The difference between IAM permissions (what I'm allowed to do to the account) and a bucket policy (what other services or the public are allowed to do to one specific resource). These sound similar at first but they're two completely different layers.
- Why it's worth separating a root account from daily admin work with MFA, even on a personal learning account where nobody else is involved.

## What's next

This is the first project in a series. Next one is a serverless contact form backend using API Gateway, Lambda, DynamoDB and SES, built and documented separately from this one.
