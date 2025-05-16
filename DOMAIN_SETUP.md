# Setting Up Your Custom Domain

This document explains how to connect your custom domain (medicalmicroapps.com) to your Render deployment.

## Steps to Configure Your Domain

1. **Verify Domain in Render**:
   - Sign in to your Render dashboard
   - Select your microapps service
   - Go to "Settings" → "Custom Domains"
   - Add both "medicalmicroapps.com" and "www.medicalmicroapps.com"
   - Render will provide you with DNS records to add to your domain registrar

2. **Configure DNS at Your Domain Registrar**:
   - Log in to your domain registrar (where you purchased medicalmicroapps.com)
   - Go to DNS settings or DNS management
   - Add the CNAME records provided by Render:
     
     For the apex domain (medicalmicroapps.com):
     ```
     Type: ALIAS or ANAME (if supported) or A records
     Value: [IP addresses provided by Render]
     ```
     
     For the www subdomain:
     ```
     Type: CNAME
     Name: www
     Value: [your-app-name].onrender.com
     ```

3. **Wait for DNS Propagation**:
   - DNS changes can take 24-48 hours to fully propagate
   - You can check propagation using tools like [dnschecker.org](https://dnschecker.org)

4. **Verify SSL Certificate**:
   - Render will automatically provision an SSL certificate for your domain
   - This may take some time after the DNS records have propagated

## Troubleshooting

If your domain isn't working after 48 hours:

1. Verify that DNS records match exactly what Render provided
2. Check the Render dashboard for any verification errors
3. Contact Render support if issues persist

## Additional Resources

- [Render Custom Domains Documentation](https://render.com/docs/custom-domains)
- [Understanding DNS Records](https://render.com/docs/dns) 