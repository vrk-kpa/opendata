import {aws_certificatemanager as acm, aws_route53 as route53, Stack} from "aws-cdk-lib";
import {Construct} from "constructs";
import {CertificateStackProps} from "./certificate-stack-props";

export class CertificateStack extends Stack {
  readonly certificate: acm.ICertificate;
  constructor(scope: Construct, id: string, props: CertificateStackProps) {
    super(scope, id, props);

    const validationZones: {[key: string]:  route53.IHostedZone } = {}

    validationZones[props.zone.zoneName] = props.zone

    const subjectAlternativeNames: string[] = []

    props.oldDomains.forEach((domain, index) => {
      subjectAlternativeNames.push(domain.webFqdn)
      subjectAlternativeNames.push(domain.rootFqdn)

      let zone = route53.HostedZone.fromLookup(this, `Zone-${index}`, {
        domainName: domain.rootFqdn,
      })
      
      validationZones[domain.webFqdn] = zone
      validationZones[domain.rootFqdn] = zone
    })

    this.certificate = new acm.Certificate(this, 'Certificate', {
      domainName: props.zone.zoneName,
      subjectAlternativeNames: subjectAlternativeNames,
      validation: acm.CertificateValidation.fromDnsMultiZone(validationZones)
    })
  }
}
