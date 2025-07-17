package com.example.secondprogram;
import androidx.appcompat.app.AppCompatActivity;
import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.text.TextUtils;
import android.widget.Button;
import android.widget.EditText;
import android.widget.Toast;

public class MainActivity extends AppCompatActivity {
    private EditText name;
    private EditText password;
    private Button login;
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        name = findViewById(R.id.etUsername);
        password = findViewById(R.id.etPassword);
        login  = findViewById(R.id.btnLogin);
        login.setOnClickListener(new View.OnClickListener() {
             @Override
             public void onClick(View v) {
                 validatelogin();
             }
         });
    }

    private void validatelogin()
    {
        String user = name.getText().toString().trim();
        String pass = password.getText().toString().trim();
        if (TextUtils.isEmpty(user)|| TextUtils.isEmpty(pass))
        {
            Toast.makeText(this,"Cannot be empty",Toast.LENGTH_SHORT).show();
        }
        else {
            if(user.equals("admin")&&pass.equals("123"))
            {
                Toast.makeText(this,"Login successful",Toast.LENGTH_SHORT).show();
            }
            else {
                Toast.makeText(this,"Login unsuccessful",Toast.LENGTH_SHORT).show();
            }
        }
    }
}
