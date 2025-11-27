#!/bin/bash
# Script para configurar LibreOffice para respeitar fontes do DOCX

# Criar diretório de config se não existir
mkdir -p ~/.config/libreoffice/4/user

# Criar registrymodifications.xcu
cat > ~/.config/libreoffice/4/user/registrymodifications.xcu << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<oor:items xmlns:oor="http://openoffice.org/2001/registry" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <item oor:path="/org.openoffice.Office.Common/Filter/Microsoft/Import">
    <prop oor:name="ImportWWFieldsAsEnhancedFields" oor:op="fuse">
      <value>true</value>
    </prop>
    <prop oor:name="CharBackgroundToHighlighting" oor:op="fuse">
      <value>false</value>
    </prop>
  </item>
  <item oor:path="/org.openoffice.Office.Common/Save/Document">
    <prop oor:name="EmbedFonts" oor:op="fuse">
      <value>true</value>
    </prop>
  </item>
</oor:items>
EOF

echo "LibreOffice configurado para respeitar fontes embarcadas"
