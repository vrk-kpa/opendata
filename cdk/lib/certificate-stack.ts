import {aws_certificatemanager as acm, aws_route53 as route53, Stack} from "aws-cdk-lib";
import {Construct} from "constructs";
import {CommonStackProps} from "./common-stack-props";

export class CertificateStack extends Stack {
  readonly zone: route53.IHostedZone;
  readonly secondaryZone: route53.IHostedZone;
  readonly certificate: acm.ICertificate;
  constructor(scope: Construct, id: string, props: CommonStackProps) {
    super(scope, id, props);

    this.zone = route53.HostedZone.fromLookup(this, 'Avoindatafi', {
      domainName: props.fqdn
    })
    this.secondaryZone = route53.HostedZone.fromLookup(this, 'Opendatafi', {
      domainName: props.secondaryFqdn
    })

    const alternativeNamePrefixes: string[] = [
      "www",
      "vip"
    ]

    const alternativeNames: string[] = alternativeNamePrefixes.map((name) => {
      return name + "." + this.zone.zoneName
    })

    const secondaryAlternativeNames: string[] = alternativeNamePrefixes.map((name) => {
      return name + "." + this.secondaryZone.zoneName
    })

    secondaryAlternativeNames.push(this.secondaryZone.zoneName)

    const validationZones: {[key: string]:  route53.IHostedZone }= {
      "avoindata.fi": this.zone
    }
    alternativeNames.forEach((name) => {
      validationZones[name] = this.zone
    })

    secondaryAlternativeNames.forEach((name) => {
      validationZones[name] = this.secondaryZone
    })


    this.certificate = new acm.Certificate(this, 'Certificate', {
      domainName: this.zone.zoneName,
      subjectAlternativeNames: alternativeNames.concat(secondaryAlternativeNames),
      validation: acm.CertificateValidation.fromDnsMultiZone(validationZones)
    })
  }
}
