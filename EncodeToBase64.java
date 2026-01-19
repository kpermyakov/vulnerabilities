package org.example;

import java.io.*;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.Base64;

public class EncodeToBase64 {

    public static void main(String[] args) {
        String inputFilePath = "d:\\output48.xlsx";
        String outputBase64Path = "d:\\bs_2.base64";

        try {
            byte[] fileContent = Files.readAllBytes(new File(inputFilePath).toPath());

            byte[] fileNameBytes = "output.xlsx".getBytes(StandardCharsets.UTF_8);

            // иконок нет → пустые
            byte[] icon16 = new byte[0];
            byte[] icon32 = new byte[0];

            int totalSize =
                    4 + fileNameBytes.length +
                            4 + icon16.length +
                            4 + icon32.length +
                            4 + fileContent.length;

            ByteBuffer buffer = ByteBuffer.allocate(totalSize);
            buffer.order(ByteOrder.LITTLE_ENDIAN);

            buffer.putInt(fileNameBytes.length);
            buffer.put(fileNameBytes);

            buffer.putInt(icon16.length);
            buffer.put(icon16);

            buffer.putInt(icon32.length);
            buffer.put(icon32);

            buffer.putInt(fileContent.length);
            buffer.put(fileContent);

            byte[] resultBytes = buffer.array();

            String base64 = Base64.getEncoder().encodeToString(resultBytes);

            try (BufferedWriter writer = new BufferedWriter(new FileWriter(outputBase64Path))) {
                writer.write(base64);
            }

            System.out.println("Base64 создан: " + outputBase64Path);

        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
