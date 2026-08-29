import { QRCodeSVG } from 'qrcode.react'

const LAN_IP = import.meta.env.VITE_LAN_IP || window.location.hostname

export default function QrPanel() {
  const submitUrl = `http://${LAN_IP}:5173/submit`

  return (
    <div className="qr-panel">
      <QRCodeSVG value={submitUrl} size={90} bgColor="#1e1812" fgColor="#f2ede6" />
      <div className="qr-panel-text">
        <span>Scan to add a test transaction</span>
        <span className="qr-url">{submitUrl}</span>
      </div>
    </div>
  )
}