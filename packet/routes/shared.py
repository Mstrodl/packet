from flask import render_template
from datetime import datetime
from itertools import chain

from packet import auth, app
from packet.models import Freshman, Packet
from packet.packet import get_signatures, get_number_required, get_number_signed
from packet.utils import before_request, signed_packet


@app.route("/packet/<uid>")
@auth.oidc_auth
@before_request
def freshman_packet(uid, info=None):
    freshman = Freshman.query.filter_by(rit_username=uid).first()
    signatures = get_signatures(uid)
    required = sum(get_number_required(uid).values())
    signed = sum(get_number_signed(uid).values())
    packet_signed = signed_packet(info['uid'], uid)
    return render_template("packet.html", info=info, signatures=signatures, uid=uid, required=required, signed=signed,
                           freshman=freshman, packet_signed=packet_signed)


@app.route("/packets")
@auth.oidc_auth
@before_request
def packets(info=None):
    packets = Packet.query.filter(Packet.end > datetime.now()).filter(Packet.start < datetime.now()).all()

    # Add the did_sign flag
    if app.config["REALM"] == "csh":
        # User is an upperclassman
        for packet in packets:
            for sig in chain(packet.upper_signatures, packet.misc_signatures):
                packet.did_sign = sig.signed and sig.member == info["uid"]
    else:
        # User is a freshman
        for packet in packets:
            for sig in packet.fresh_signatures:
                packet.did_sign = sig.signed and sig.freshman_username == info["uid"]

    return render_template("active_packets.html", info=info, packets=packets)
